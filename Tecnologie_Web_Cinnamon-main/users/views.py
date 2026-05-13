from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import UserProfile, FriendRequest, Friendship, Notification
from user_messages.models import Message


# ---------------------------------------------------------------------------
# Context processor — unread messages count badge (used in settings.py)
# ---------------------------------------------------------------------------

def unread_messages_count(request):
    """Context processor: inject unread message count into every template."""
    if request.user.is_authenticated:
        count = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
        return {'unread_messages_count': count}
    return {'unread_messages_count': 0}


# ---------------------------------------------------------------------------
# Authentication & Registration
# ---------------------------------------------------------------------------

def register(request):
    """User registration: creates User + UserProfile."""
    if request.user.is_authenticated:
        return redirect('recipes-home')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account creato per {username}! Ora puoi accedere.')
            return redirect('user-login')
    else:
        form = UserRegisterForm()

    return render(request, 'users/register.html', {'form': form})


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@login_required
def profile(request):
    """Personal profile dashboard."""
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    pending_friend_requests = FriendRequest.objects.filter(
        to_user=request.user, status='pending'
    ).count()

    context = {
        'profile': profile_obj,
        'pending_friend_requests': pending_friend_requests,
    }
    return render(request, 'users/profile.html', context)


@login_required
def update_profile(request):
    """Update user account info and profile details."""
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile_obj)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Profilo aggiornato con successo!')
            return redirect('user-profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile_obj)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'profile': profile_obj,
    }
    return render(request, 'users/update_profile.html', context)


def public_profile(request, username):
    """Public profile view with privacy enforcement."""
    profile_user = get_object_or_404(User, username=username)
    profile_obj = get_object_or_404(UserProfile, user=profile_user)

    # Privacy: private profiles are visible only to owner and friends
    if not profile_obj.is_public and request.user != profile_user:
        if not request.user.is_authenticated or not Friendship.are_friends(request.user, profile_user):
            messages.warning(request, 'Questo profilo è privato.')
            return redirect('recipes-home')

    # Determine friendship/request status
    is_friend = False
    friend_request_sent = None
    friend_request_received = None

    if request.user.is_authenticated and request.user != profile_user:
        is_friend = Friendship.are_friends(request.user, profile_user)
        if not is_friend:
            friend_request_sent = FriendRequest.objects.filter(
                from_user=request.user, to_user=profile_user, status='pending'
            ).first()
            friend_request_received = FriendRequest.objects.filter(
                from_user=profile_user, to_user=request.user, status='pending'
            ).first()

    # Visible recipes
    from recipes.models import Recipe
    if request.user == profile_user:
        recipes = Recipe.objects.filter(author=profile_user).order_by('-created_at')
    elif is_friend:
        recipes = Recipe.objects.filter(author=profile_user).exclude(
            visibility='private'
        ).order_by('-created_at')
    else:
        recipes = Recipe.objects.filter(
            author=profile_user, visibility='public'
        ).order_by('-created_at')

    total_recipes = recipes.count()

    context = {
        'profile_user': profile_user,
        'profile': profile_obj,
        'recipes': recipes[:6],
        'total_recipes': total_recipes,
        'is_friend': is_friend,
        'friend_request_sent': friend_request_sent,
        'friend_request_received': friend_request_received,
    }
    return render(request, 'users/public_profile.html', context)


# ---------------------------------------------------------------------------
# User Search
# ---------------------------------------------------------------------------

def user_search(request):
    """Search users by username/bio/interests, experience level and specialty."""
    query = request.GET.get('q', '').strip()
    experience = request.GET.get('experience', '').strip()
    specialty = request.GET.get('specialty', '').strip()

    users = User.objects.select_related('userprofile').filter(
        userprofile__isnull=False
    ).exclude(id=request.user.id if request.user.is_authenticated else 0)

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(userprofile__bio__icontains=query) |
            Q(userprofile__culinary_interests__icontains=query)
        )

    if experience:
        users = users.filter(userprofile__experience_level=experience)

    if specialty:
        users = users.filter(userprofile__cuisine_specialties__icontains=specialty)

    # Only show public profiles (or the user's own profile)
    users = users.filter(userprofile__is_public=True)

    context = {
        'users': users.distinct()[:50],
        'query': query,
        'experience': experience,
        'specialty': specialty,
        'experience_choices': UserProfile.EXPERIENCE_CHOICES,
        'specialty_choices': UserProfile.CUISINE_SPECIALTIES,
    }
    return render(request, 'users/search.html', context)


# ---------------------------------------------------------------------------
# Friend System
# ---------------------------------------------------------------------------

@login_required
def friends_list(request):
    """List all friends of the logged-in user."""
    friends = Friendship.get_friends(request.user)
    pending_friend_requests = FriendRequest.objects.filter(
        to_user=request.user, status='pending'
    ).count()

    context = {
        'friends': friends,
        'pending_friend_requests': pending_friend_requests,
    }
    return render(request, 'users/friends_list.html', context)


@login_required
def friend_requests(request):
    """Show received and sent friend requests."""
    received_requests = FriendRequest.objects.filter(
        to_user=request.user, status='pending'
    ).select_related('from_user', 'from_user__userprofile').order_by('-created_at')

    sent_requests = FriendRequest.objects.filter(
        from_user=request.user, status='pending'
    ).select_related('to_user', 'to_user__userprofile').order_by('-created_at')

    context = {
        'received_requests': received_requests,
        'sent_requests': sent_requests,
    }
    return render(request, 'users/friend_requests.html', context)


@login_required
def send_friend_request(request, username):
    """Send a friend request to a user."""
    to_user = get_object_or_404(User, username=username)

    if to_user == request.user:
        messages.error(request, 'Non puoi inviare una richiesta di amicizia a te stesso.')
        return redirect('user-public-profile', username=username)

    if Friendship.are_friends(request.user, to_user):
        messages.info(request, f'Sei già amico di {to_user.username}.')
        return redirect('user-public-profile', username=username)

    existing = FriendRequest.objects.filter(
        from_user=request.user, to_user=to_user
    ).first()

    if existing:
        if existing.status == 'pending':
            messages.info(request, 'Hai già inviato una richiesta di amicizia.')
        elif existing.status == 'rejected':
            existing.status = 'pending'
            existing.save()
            messages.success(request, f'Richiesta di amicizia inviata a {to_user.username}!')
    else:
        FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        messages.success(request, f'Richiesta di amicizia inviata a {to_user.username}!')

    return redirect('user-public-profile', username=username)


@login_required
def accept_friend_request(request, request_id):
    """Accept a pending friend request."""
    if request.method == 'POST':
        friend_request = get_object_or_404(
            FriendRequest, id=request_id, to_user=request.user, status='pending'
        )
        friend_request.accept()
        messages.success(
            request,
            f'Sei ora amico di {friend_request.from_user.username}!'
        )
    return redirect('user-friend-requests')


@login_required
def reject_friend_request(request, request_id):
    """Reject a pending friend request."""
    if request.method == 'POST':
        friend_request = get_object_or_404(
            FriendRequest, id=request_id, to_user=request.user, status='pending'
        )
        friend_request.reject()
        messages.info(
            request,
            f'Richiesta di amicizia di {friend_request.from_user.username} rifiutata.'
        )
    return redirect('user-friend-requests')


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@login_required
def notifications_list(request):
    """Display all notifications for the logged-in user and mark them as read."""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')

    # Mark all as read on page visit
    notifications.filter(is_read=False).update(is_read=True)

    return render(request, 'users/notifications.html', {'notifications': notifications})
