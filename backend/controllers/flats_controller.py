"""Mieszkania, członkostwa i zaproszenia."""

from __future__ import annotations

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user, login_required

from backend.audit import audit_event
from backend.forms.flat_forms import DeleteFlatForm, EmptyActionForm, FlatForm
from backend.models import MembershipStatus
from backend.security.access import flat_admin_required, flat_member_required
from backend.services.flat_service import (
    AdminTransferRequired,
    FlatAccessDenied,
    FlatNameMismatch,
    FlatService,
    InvalidMembershipTransition,
    InviteUnavailable,
    LastAdminMustDelete,
    MembershipNotFound,
)

bp = Blueprint("flats", __name__, url_prefix="/flats")
join_bp = Blueprint("join", __name__)


@bp.get("")
@login_required
def index() -> str:
    return render_template(
        "pages/flats/index.html",
        flats=FlatService().list_for_user(current_user.id),
    )


@bp.route("/new", methods=["GET", "POST"])
@login_required
def create() -> str:
    form = FlatForm()
    if form.validate_on_submit():
        flat = FlatService().create(form.name.data, current_user.id)
        flash("Utworzono mieszkanie. Jesteś jego administratorem.", "success")
        return redirect(url_for("flats.detail", flat_id=flat.id))
    return render_template("pages/flats/new.html", form=form)


@bp.get("/<int:flat_id>")
@flat_member_required
def detail(flat_id: int) -> str:
    members = FlatService().list_members(flat_id)
    return render_template(
        "pages/flats/detail.html",
        flat=g.flat,
        members=members,
        membership=g.membership,
        leave_form=EmptyActionForm(),
    )


@bp.post("/<int:flat_id>/leave")
@flat_member_required
def leave(flat_id: int):
    try:
        FlatService().leave(flat_id, current_user.id)
    except LastAdminMustDelete:
        flash("To ostatni administrator. Potwierdź usunięcie mieszkania, aby z niego odejść.", "warning")
        return redirect(url_for("flats.delete", flat_id=flat_id))
    except AdminTransferRequired:
        flash("Przed opuszczeniem mieszkania przekaż rolę administratora innej osobie.", "warning")
        return redirect(url_for("flats.detail", flat_id=flat_id))
    flash("Opuszczono mieszkanie.", "info")
    return redirect(url_for("flats.index"))


@bp.get("/<int:flat_id>/members")
@flat_member_required
def members(flat_id: int) -> str:
    return render_template(
        "pages/flats/members.html",
        flat=g.flat,
        memberships=FlatService().list_members(flat_id, include_requests=g.membership.is_admin),
        membership=g.membership,
        action_form=EmptyActionForm(),
    )


@bp.post("/<int:flat_id>/members/<int:membership_id>/approve")
@flat_admin_required
def approve_member(flat_id: int, membership_id: int):
    try:
        FlatService().approve_member(flat_id, membership_id, current_user.id)
    except MembershipNotFound:
        abort(404)
    except (FlatAccessDenied, InvalidMembershipTransition):
        flash("Nie można zaakceptować tego członkostwa.", "warning")
    else:
        flash("Zaakceptowano prośbę o dołączenie.", "success")
    return redirect(url_for("flats.members", flat_id=flat_id))


@bp.post("/<int:flat_id>/members/<int:membership_id>/reject")
@flat_admin_required
def reject_member(flat_id: int, membership_id: int):
    try:
        FlatService().reject_member(flat_id, membership_id, current_user.id)
    except MembershipNotFound:
        abort(404)
    except (FlatAccessDenied, InvalidMembershipTransition):
        flash("Nie można odrzucić tej prośby.", "warning")
    else:
        flash("Odrzucono prośbę o dołączenie.", "info")
    return redirect(url_for("flats.members", flat_id=flat_id))


@bp.post("/<int:flat_id>/members/<int:membership_id>/remove")
@flat_admin_required
def remove_member(flat_id: int, membership_id: int):
    try:
        FlatService().remove_member(flat_id, membership_id, current_user.id)
    except MembershipNotFound:
        abort(404)
    except (FlatAccessDenied, InvalidMembershipTransition):
        flash("Nie można usunąć tego członkostwa.", "warning")
    else:
        flash("Usunięto członka lub odrzuconą prośbę.", "success")
    return redirect(url_for("flats.members", flat_id=flat_id))


@bp.post("/<int:flat_id>/members/<int:membership_id>/make-admin")
@flat_admin_required
def make_admin(flat_id: int, membership_id: int):
    try:
        FlatService().make_admin(flat_id, membership_id, current_user.id)
    except MembershipNotFound:
        abort(404)
    except (FlatAccessDenied, InvalidMembershipTransition):
        flash("Nie można przekazać tej osobie roli administratora.", "warning")
    else:
        flash("Przekazano rolę administratora.", "success")
    return redirect(url_for("flats.members", flat_id=flat_id))


@bp.route("/<int:flat_id>/delete", methods=["GET", "POST"])
@flat_admin_required
def delete(flat_id: int) -> str:
    form = DeleteFlatForm()
    if form.validate_on_submit():
        try:
            FlatService().delete_flat(flat_id, current_user.id, form.confirmation.data)
        except FlatNameMismatch:
            form.confirmation.errors.append("Wpisana nazwa nie pasuje do nazwy mieszkania.")
        except MembershipNotFound:
            abort(404)
        except FlatAccessDenied:
            abort(403)
        else:
            flash("Usunięto mieszkanie i powiązane dane.", "info")
            return redirect(url_for("flats.index"))
    return render_template("pages/flats/delete.html", flat=g.flat, form=form)


@bp.route("/<int:flat_id>/invites", methods=["GET", "POST"])
@flat_admin_required
def invites(flat_id: int) -> str:
    form = EmptyActionForm()
    new_invite_url = None
    if form.validate_on_submit():
        invite, token = FlatService().create_invite(flat_id, current_user.id)
        new_invite_url = url_for("join.request", token=token)
        flash(f"Link zaproszenia jest ważny do {invite.expires_at:%Y-%m-%d %H:%M} UTC.", "success")
        form = EmptyActionForm()
    return render_template(
        "pages/flats/invites.html",
        flat=g.flat,
        invites=FlatService().list_invites(flat_id),
        form=form,
        revoke_form=EmptyActionForm(),
        new_invite_url=new_invite_url,
    )


@bp.post("/<int:flat_id>/invites/<int:invite_id>/revoke")
@flat_admin_required
def revoke_invite(flat_id: int, invite_id: int):
    try:
        FlatService().revoke_invite(flat_id, invite_id, current_user.id)
    except MembershipNotFound:
        abort(404)
    except FlatAccessDenied:
        abort(403)
    flash("Unieważniono zaproszenie.", "info")
    return redirect(url_for("flats.invites", flat_id=flat_id))


@join_bp.route("/join/<token>", methods=["GET", "POST"])
@login_required
def request(token: str) -> str:
    service = FlatService()
    context = service.join_context(token, current_user.id)
    if context is None:
        audit_event("invite_rejected", reason="invalid_or_expired")
        abort(404)
    flat, membership = context
    form = EmptyActionForm()
    message = None
    if form.validate_on_submit():
        try:
            status = service.request_to_join(token, current_user.id)
        except InviteUnavailable:
            audit_event("invite_rejected", reason="invalid_or_expired")
            abort(404)
        if status is MembershipStatus.PENDING:
            message = "Prośba oczekuje na akceptację administratora."
        elif status is MembershipStatus.ACTIVE:
            message = "Jesteś już członkiem tego mieszkania."
        else:
            message = "Twoja poprzednia prośba została odrzucona. Skontaktuj się z administratorem."
        context = service.join_context(token, current_user.id)
        if context is None:
            abort(404)
        membership = context[1]
    return render_template(
        "pages/flats/join.html",
        flat=flat,
        membership=membership,
        form=form,
        message=message,
    )
