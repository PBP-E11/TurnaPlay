import uuid
from datetime import date, timedelta

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

TournamentInvite = apps.get_model("tournament_invite", "TournamentInvite")
Tournament = apps.get_model("tournaments", "Tournament")
TournamentFormat = apps.get_model("tournaments", "TournamentFormat")
Game = apps.get_model("tournaments", "Game")
TournamentRegistration = apps.get_model("tournament_registration", "TournamentRegistration")
TeamMember = apps.get_model("tournament_registration", "TeamMember")
GameAccount = apps.get_model("game_account", "GameAccount")

User = get_user_model()


# -------------------- Helper Utilities --------------------

def create_user(username, **extra):
    email = f"{username}@ex.com"
    defaults = {"email": email, "password": "pass12345"}
    defaults.update(extra)
    if hasattr(User.objects, "create_user"):
        try:
            return User.objects.create_user(username=username, email=email, password=defaults["password"])
        except TypeError:
            return User.objects.create_user(email=email, password=defaults["password"])
    return User.objects.create(username=username, email=email)


def create_game(name="VALO"):
    return Game.objects.create(name=name)


def create_format(game, team_size=5):
    fields = {f.name for f in TournamentFormat._meta.get_fields() if not f.many_to_many and not f.one_to_many}
    data = {}
    if "game" in fields:
        data["game"] = game
    if "team_size" in fields:
        data["team_size"] = team_size
    if "size" in fields and "team_size" not in fields:
        data["size"] = team_size
    if "name" in fields:
        data["name"] = f"{game.name} {team_size}v{team_size}"
    return TournamentFormat.objects.create(**data)


def create_tournament(fmt, active=True):
    """
    Buat Tournament minimalis dengan mengisi field-field umum jika ada.
    Tidak ada introspeksi default yang rumit—kalau field ada, kita isi nilai aman.
    """
    fields = {f.name for f in Tournament._meta.get_fields() if getattr(f, "concrete", False)}

    data = {}
    today = date.today()

    # FK & nama
    if "tournament_format" in fields:
        data["tournament_format"] = fmt
    if "name" in fields:
        data["name"] = f"{fmt.game.name} Cup"

    # Kuota tim
    if "team_maximum_count" in fields:
        data["team_maximum_count"] = 64
    if "team_minimum_count" in fields:
        data["team_minimum_count"] = 2

    if "location" in fields:
        data["location"] = "Online"
    if "description" in fields:
        data["description"] = "Test tournament"

    # Tanggal turnamen
    if "start_date" in fields:
        data["start_date"] = today + timedelta(days=14)
    if "end_date" in fields:
        data["end_date"] = today + timedelta(days=15)

    t = Tournament.objects.create(**data)

    if not ({"registration_open_date", "registration_close_date"} <= fields or
            {"registration_start_date", "registration_end_date"} <= fields):
        setattr(t, "is_active", bool(active))

    return t

def create_team(tournament, team_name="Team A", leader_user=None, leader_ga=None):
    team = TournamentRegistration.objects.create(tournament=tournament, team_name=team_name)
    if leader_user and leader_ga is None:
        leader_ga = GameAccount.objects.create(
            user=leader_user, game=tournament.tournament_format.game, ingame_name=f"{leader_user}-ingame"
        )
    if leader_ga:
        TeamMember.objects.create(team=team, game_account=leader_ga, is_leader=True)
    return team


def create_game_account(user, game, name_suffix=""):
    return GameAccount.objects.create(
        user=user, game=game, ingame_name=f"{user}-{name_suffix or uuid.uuid4().hex[:6]}"
    )


def set_team_full(team):
    """Isi tim hingga penuh sesuai team_size format turnamen."""
    size = getattr(team.tournament.tournament_format, "team_size", 5)
    current = team.members.count()
    for i in range(size - current):
        dummy = create_user(f"dummy{i}")
        ga = create_game_account(dummy, team.tournament.tournament_format.game)
        TeamMember.objects.create(team=team, game_account=ga, is_leader=False)


# -------------------- Tests --------------------

class TournamentInviteModelTests(TestCase):
    def setUp(self):
        self.game = create_game("MLBB")
        self.fmt = create_format(self.game, team_size=3)
        self.tournament = create_tournament(self.fmt, active=True)

        # users
        self.leader = create_user("leader")
        self.u_alice = create_user("alice")
        self.u_bob = create_user("bob")

        # accounts
        self.ga_leader = create_game_account(self.leader, self.game, "L")
        self.ga_alice = create_game_account(self.u_alice, self.game, "A")
        self.ga_bob = create_game_account(self.u_bob, self.game, "B")

        # team with leader
        self.team = create_team(self.tournament, "Alpha", leader_user=self.leader, leader_ga=self.ga_leader)

    # ---- Basic create & unique constraint ----

    def test_create_pending_invite_success_and_unique_pending(self):
        inv1 = TournamentInvite(user_account=self.u_alice, tournament_registration=self.team)
        inv1.save() 
        self.assertEqual(inv1.status, TournamentInvite.Status.PENDING)

        inv2 = TournamentInvite(user_account=self.u_alice, tournament_registration=self.team)
        with self.assertRaises(ValidationError):
            inv2.save()

        inv1.status = TournamentInvite.Status.ACCEPTED
        inv1.save(update_fields=["status"])
        inv3 = TournamentInvite(user_account=self.u_alice, tournament_registration=self.team)
        inv3.save()

    def test_str_representation(self):
        inv = TournamentInvite.objects.create(user_account=self.u_bob, tournament_registration=self.team)
        s = str(inv)
        self.assertIn("Invite to", s)
        self.assertIn("Alpha", s)
        self.assertIn(inv.get_status_display(), s)

    # ---- Guard tournament active & team capacity on CREATE ----

    def test_create_invite_denied_when_tournament_closed(self):
        tourn = create_tournament(self.fmt, active=False)
        team = create_team(tourn, "Closed Team", leader_user=self.leader, leader_ga=self.ga_leader)
        inv = TournamentInvite(user_account=self.u_alice, tournament_registration=team)
        with self.assertRaises(ValidationError):
            inv.save()

    def test_create_invite_denied_when_team_full(self):
        set_team_full(self.team)
        inv = TournamentInvite(user_account=self.u_bob, tournament_registration=self.team)
        with self.assertRaises(ValidationError):
            inv.save()

    # ---- ACCEPT flow ----

    def test_accept_invite_success_creates_team_member_and_updates_status(self):
        inv = TournamentInvite.objects.create(user_account=self.u_alice, tournament_registration=self.team)
        member = inv.accept(self.ga_alice)
        inv.refresh_from_db()
        self.assertEqual(inv.status, TournamentInvite.Status.ACCEPTED)
        self.assertTrue(
            TeamMember.objects.filter(team=self.team, game_account=self.ga_alice, is_leader=False).exists()
        )
        self.assertEqual(member.team_id, self.team.id)

    def test_accept_invite_fails_when_not_pending(self):
        inv = TournamentInvite.objects.create(
            user_account=self.u_alice, tournament_registration=self.team, status=TournamentInvite.Status.REJECTED
        )
        with self.assertRaises(ValidationError):
            inv.accept(self.ga_alice)

    def test_accept_invite_fails_when_game_mismatch(self):
        other_game = create_game("DOTA")
        ga_wrong = create_game_account(self.u_alice, other_game, "X")
        inv = TournamentInvite.objects.create(user_account=self.u_alice, tournament_registration=self.team)
        with self.assertRaises(ValidationError):
            inv.accept(ga_wrong)

    def test_accept_invite_fails_when_user_already_in_other_team_same_tournament(self):
        other_team = create_team(self.tournament, "Bravo", leader_user=self.u_bob, leader_ga=self.ga_bob)
        TeamMember.objects.create(team=other_team, game_account=self.ga_alice, is_leader=False)

        inv = TournamentInvite.objects.create(user_account=self.u_alice, tournament_registration=self.team)
        with self.assertRaises(ValidationError):
            inv.accept(self.ga_alice)

    def test_accept_invite_fails_when_team_full(self):
        set_team_full(self.team)
        inv = TournamentInvite.objects.create(user_account=self.u_bob, tournament_registration=self.team)
        with self.assertRaises(ValidationError):
            inv.accept(self.ga_bob)

    def test_accept_invite_fails_when_tournament_closed(self):
        tourn = create_tournament(self.fmt, active=False)
        team_closed = create_team(tourn, "Closed", leader_user=self.leader, leader_ga=self.ga_leader)
        inv = TournamentInvite.objects.create(user_account=self.u_bob, tournament_registration=team_closed)
        with self.assertRaises(ValidationError):
            inv.accept(self.ga_bob)

    def test_accept_invite_requires_account_owner(self):
        inv = TournamentInvite.objects.create(user_account=self.u_alice, tournament_registration=self.team)
        with self.assertRaises(ValidationError):
            inv.accept(self.ga_bob)

    # ---- REJECT flow ----

    def test_reject_invite_changes_status(self):
        inv = TournamentInvite.objects.create(user_account=self.u_bob, tournament_registration=self.team)
        inv.reject()
        inv.refresh_from_db()
        self.assertEqual(inv.status, TournamentInvite.Status.REJECTED)

    # ---- Model-level clean() prevents sending invite to member of another team ----

    def test_clean_blocks_invite_if_user_already_joined_other_team(self):
        tourn = self.tournament
        other_team = create_team(tourn, "Gamma", leader_user=self.u_alice, leader_ga=self.ga_alice)
        TeamMember.objects.create(team=other_team, game_account=self.ga_bob, is_leader=False)

        inv = TournamentInvite(user_account=self.u_bob, tournament_registration=self.team)
        with self.assertRaises(ValidationError):
            inv.save()