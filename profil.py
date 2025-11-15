from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from sqlalchemy import func
from models import User, Video, Follow
from extensions import db

# -------------------------
# Blueprint pour les profils
# -------------------------
profil_bp = Blueprint("profil", __name__, url_prefix="/u")  # /u/<username>

# -------------------------
# Afficher le profil
# -------------------------
@profil_bp.route("/<username>")
def show_profil(username):
    # Recherche insensible à la casse
    user = User.query.filter(func.lower(User.username) == username.lower()).first()
    if not user:
        abort(404, description="Utilisateur non trouvé")

    # Récupère toutes les vidéos
    videos = Video.query.filter_by(author_id=user.id).order_by(Video.created_at.desc()).all()

    # Vérifie si l'utilisateur courant suit ce profil
    is_following = False
    if current_user.is_authenticated and current_user.id != user.id:
        # Il faut s'assurer que User a bien une méthode is_following
        is_following = current_user.is_following(user)

    return render_template(
        "profil.html",
        user=user,
        videos=videos,
        is_following=is_following
    )

# -------------------------
# S'abonner à un utilisateur
# -------------------------
@profil_bp.route("/follow/<int:user_id>", methods=["POST"])
@login_required
def follow_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("Vous ne pouvez pas vous abonner à vous-même.", "warning")
        return redirect(url_for("profil.show_profil", username=user.username))

    if current_user.is_following(user):
        flash(f"Vous suivez déjà {user.display_name or user.username}.", "info")
    else:
        follow = Follow(follower_id=current_user.id, followed_id=user.id)
        db.session.add(follow)
        db.session.commit()
        flash(f"Vous suivez maintenant {user.display_name or user.username}.", "success")

    return redirect(url_for("profil.show_profil", username=user.username))

# -------------------------
# Se désabonner d'un utilisateur
# -------------------------
@profil_bp.route("/unfollow/<int:user_id>", methods=["POST"])
@login_required
def unfollow_user(user_id):
    user = User.query.get_or_404(user_id)
    follow = Follow.query.filter_by(
        follower_id=current_user.id, 
        followed_id=user.id
    ).first()

    if follow:
        db.session.delete(follow)
        db.session.commit()
        flash(f"Vous avez arrêté de suivre {user.display_name or user.username}.", "info")
    else:
        flash(f"Vous ne suivez pas {user.display_name or user.username}.", "warning")

    return redirect(url_for("profil.show_profil", username=user.username))

# -------------------------
# Optionnel : route de test
# -------------------------
@profil_bp.route("/test")
def test_route():
    return "Blueprint profil opérationnel ✅"
