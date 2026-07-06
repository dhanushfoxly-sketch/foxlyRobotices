from django.shortcuts import render
from .models import BoardType, Component, Project, DownloadRequest
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from .forms import UploadZipForm, DownloadRequestForm, DownloadCodeForm
from django.conf import settings
from django.core.mail import send_mail
from django.http import FileResponse, Http404
import zipfile
import os
from datetime import datetime
from django.core.files import File as DjangoFile
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from urllib.parse import quote_plus
import logging

logger = logging.getLogger(__name__)


def index(request):
    featured_projects = Project.objects.filter(featured=True)[:3]
    stats = {
        'product_count': Project.objects.count(),
        'board_count': BoardType.objects.count(),
        'component_count': Component.objects.count(),
    }
    return render(request, 'index.html', {
        'featured_projects': featured_projects,
        'stats': stats,
    })


def about(request):
    return render(request, 'about.html')


def categories(request):
    board_types = BoardType.objects.all()
    selected_board = request.GET.get('board')
    projects = Project.objects.select_related('board_type')
    
    if selected_board:
        projects = projects.filter(board_type_id=selected_board)
    
    return render(request, 'categories.html', {
        'board_types': board_types,
        'selected_board': selected_board,
        'projects': projects,
    })


def products(request):
    board_types = BoardType.objects.all()
    selected_board = request.GET.get('board')
    projects = Project.objects.select_related('board_type').prefetch_related('components')
    
    if selected_board:
        projects = projects.filter(board_type_id=selected_board)
    
    return render(request, 'products.html', {
        'board_types': board_types,
        'selected_board': selected_board,
        'projects': projects,
    })


@login_required
def upload_zip(request):
    if request.method == 'POST':
        form = UploadZipForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = request.FILES['zip_file']
            title = form.cleaned_data['title']
            bt = form.cleaned_data['board_type']

            # extract to media/projects/project_<timestamp>_<sanitized_title>
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            base_name = safe_name or os.path.splitext(os.path.basename(uploaded.name))[0]
            folder_name = f"project_{timestamp}_{base_name}"
            target_root = os.path.join(settings.MEDIA_ROOT, 'projects', folder_name)
            os.makedirs(target_root, exist_ok=True)

            try:
                with zipfile.ZipFile(uploaded) as zf:
                    zf.extractall(target_root)
            except Exception:
                form.add_error('zip_file', 'Invalid ZIP file')
                return render(request, 'upload_zip.html', {'form': form})

            # read README for description
            description = ''
            for name in ('README.md', 'README.txt', 'readme.md', 'readme.txt'):
                candidate = os.path.join(target_root, name)
                if os.path.exists(candidate):
                    try:
                        with open(candidate, 'r', encoding='utf-8') as f:
                            description = f.read()
                    except Exception:
                        description = ''
                    break

            # find first image
            image_path = None
            for root, dirs, files in os.walk(target_root):
                for fname in files:
                    if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        image_path = os.path.join(root, fname)
                        break
                if image_path:
                    break

            # create the project directly using provided board type
            proj = Project.objects.create(title=title, board_type=bt, description=description or '')
            # save the uploaded zip to the project
            try:
                proj.zip_file.save(uploaded.name, uploaded, save=True)
            except Exception:
                pass
            if image_path:
                try:
                    with open(image_path, 'rb') as f:
                        django_file = DjangoFile(f)
                        proj.image.save(os.path.basename(image_path), django_file, save=True)
                except Exception:
                    pass

            return redirect(reverse('products'))
    else:
        form = UploadZipForm()
    return render(request, 'upload_zip.html', {'form': form})


@login_required
def request_download(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    success = False
    whatsapp_url = None

    if request.method == 'POST':
        form = DownloadRequestForm(request.POST)
        if form.is_valid():
            download_request = DownloadRequest.objects.create(
                project=project,
                user=request.user,
                name=request.user.get_full_name() or request.user.username,
                email=request.user.email or None,
                phone_number=form.cleaned_data.get('phone_number'),
                message=form.cleaned_data.get('message', ''),
            )

            admin_email = getattr(settings, 'ADMIN_EMAIL', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
            if admin_email:
                subject = f"Download code request for {project.title}"
                body_lines = [
                    f"Project: {project.title}",
                    f"Requester: {download_request.name}",
                    f"User ID: {request.user.id}",
                    f"Email: {download_request.email or 'N/A'}",
                    f"Phone: {download_request.phone_number or 'N/A'}",
                    f"Message: {download_request.message or 'No message provided.'}",
                    f"Request created at: {download_request.created_at}",
                    f"Admin URL: {request.build_absolute_uri(reverse('admin:myapp_downloadrequest_change', args=[download_request.id]))}",
                ]
                send_mail(subject, '\n'.join(body_lines), settings.DEFAULT_FROM_EMAIL, [admin_email], fail_silently=True)

            twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            twilio_from = getattr(settings, 'TWILIO_WHATSAPP_FROM', None)
            whatsapp_number = getattr(settings, 'WHATSAPP_NUMBER', None)
            whatsapp_text = (
                f"Download code request for {project.title}\n"
                f"Name: {download_request.name}\n"
                f"Email: {download_request.email or 'N/A'}\n"
                f"Phone: {download_request.phone_number or 'N/A'}\n"
                f"Message: {download_request.message or 'No message provided.'}"
            )

            if twilio_sid and twilio_token and twilio_from and whatsapp_number:
                try:
                    from twilio.rest import Client
                    client = Client(twilio_sid, twilio_token)
                    client.messages.create(
                        body=whatsapp_text,
                        from_=f'whatsapp:{twilio_from}',
                        to=f'whatsapp:{whatsapp_number}',
                    )
                except Exception as exc:
                    logger.exception('Failed to send WhatsApp notification via Twilio')
                    whatsapp_url = f"https://wa.me/{whatsapp_number.lstrip('+')}?text={quote_plus(whatsapp_text)}"
            elif whatsapp_number:
                whatsapp_url = f"https://wa.me/{whatsapp_number.lstrip('+')}?text={quote_plus(whatsapp_text)}"

            success = True
    else:
        form = DownloadRequestForm()

    return render(request, 'download_request.html', {
        'project': project,
        'form': form,
        'success': success,
        'whatsapp_url': whatsapp_url,
    })


@login_required
def verify_download(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    error = None

    if request.method == 'POST':
        form = DownloadCodeForm(request.POST)
        if form.is_valid():
            access_code = form.cleaned_data['access_code']
            download_request = DownloadRequest.objects.filter(
                project=project,
                user=request.user,
                access_code=access_code,
                is_approved=True,
            ).order_by('-created_at').first()

            if download_request:
                if download_request.is_used:
                    error = 'This code has already been used. Please request a new code if needed.'
                elif not project.zip_file:
                    error = 'The requested project ZIP file is not available.'
                else:
                    zip_path = project.zip_file.path
                    if not os.path.exists(zip_path):
                        raise Http404('ZIP file not found.')
                    response = FileResponse(open(zip_path, 'rb'), as_attachment=True, filename=os.path.basename(zip_path))
                    download_request.is_used = True
                    download_request.save(update_fields=['is_used'])
                    return response
            else:
                error = 'Invalid code or contact details. Please check the information and try again.'
    else:
        form = DownloadCodeForm()

    return render(request, 'download_verify.html', {
        'project': project,
        'form': form,
        'error': error,
    })


@login_required
def my_requests(request):
    requests = DownloadRequest.objects.filter(user=request.user).select_related('project')
    return render(request, 'my_requests.html', {
        'requests': requests,
    })


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Your account has been created. You are now logged in.')
            return redirect('products')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Logged in successfully.')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('products')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('index')
    project = get_object_or_404(Project, id=project_id)
    error = None

    if request.method == 'POST':
        form = DownloadCodeForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            phone_number = form.cleaned_data.get('phone_number')
            access_code = form.cleaned_data['access_code']
            request_qs = DownloadRequest.objects.filter(
                project=project,
                access_code=access_code,
                is_approved=True,
            )
            if email:
                request_qs = request_qs.filter(email__iexact=email)
            if phone_number:
                request_qs = request_qs.filter(phone_number__iexact=phone_number)

            download_request = request_qs.order_by('-created_at').first()
            if download_request:
                if download_request.is_used:
                    error = 'This code has already been used. Please request a new code if needed.'
                elif not project.zip_file:
                    error = 'The requested project ZIP file is not available.'
                else:
                    zip_path = project.zip_file.path
                    if not os.path.exists(zip_path):
                        raise Http404('ZIP file not found.')
                    response = FileResponse(open(zip_path, 'rb'), as_attachment=True, filename=os.path.basename(zip_path))
                    download_request.is_used = True
                    download_request.save(update_fields=['is_used'])
                    return response
            else:
                error = 'Invalid code or contact details. Please check the information and try again.'
    else:
        form = DownloadCodeForm()

    return render(request, 'download_verify.html', {
        'project': project,
        'form': form,
        'error': error,
    })
