from django.shortcuts import render , redirect
from django.http import HttpResponse
from .forms import RegistrationForm
from .models import Account
from django.contrib import messages , auth
from django.contrib.auth.decorators import login_required

#verification requirements
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode , urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.conf import settings

from carts.views import _cart_id
from carts.models import Cart
from carts.models import CartItem
import pip._vendor.requests as requests


# Create your views here.

def register(request):
  if request.method == 'POST':
    form = RegistrationForm(request.POST)
    if form.is_valid():
      first_name = form.cleaned_data['first_name']
      last_name = form.cleaned_data['last_name']
      phone_number = form.cleaned_data['phone_number']
      email = form.cleaned_data['email']
      password = form.cleaned_data['password']
      username = email.split('@')[0]
      
      user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email,username=username, password=password)
      user.phone_number = phone_number
      user.save()
      
      #user authentication#
      current_site = get_current_site(request)
      mail_subject = 'Please activate your account'
      message = render_to_string('accounts/account_verification_mail.html',{
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
      })
      to_email = email
      send_email = EmailMessage(mail_subject, message, to=[to_email])
      send_email.send()
      
      # messages.success(request, 'Account Created Successfully, we have sent you an email to verify your account')
      return redirect('/accounts/login/?command=verification&email='+email)
  else:   #it is get method(render the registration form)
      form = RegistrationForm()
  context = {
            'form': form,
          }
  return render(request, 'accounts/register.html', context)

def login(request):
  if request.method == 'POST':
    email = request.POST['email']
    password = request.POST['password']
    
    user = auth.authenticate(email=email, password=password)
    
    if user is not None:
      try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        is_cart_item_exists = CartItem.objects.filter(cart=cart).exists() #we don't need product bcos we are only getting the product that was added to cart
        if is_cart_item_exists:
          cart_item = CartItem.objects.filter(cart=cart)
          
          #getting the product variation by cart id
          product_variation = []
          for item in cart_item:
             variation = item.variations.all()
             product_variation.append(list(variation))
             #get the cart item from the user to access his variations
          cart_item = CartItem.objects.filter(user=user)
          ex_var_list = []
          id = []
          for item in cart_item:
                    existing_variation = item.variations.all()
                    ex_var_list.append(list(existing_variation)) #query set convert to list
                    id.append(item.id)   
          for product in product_variation:
             if product in ex_var_list:
               index = ex_var_list.index(product)
               item_id = id[index]
               item = CartItem.objects.get(id=item_id)
               item.quantity += 1
               item.user = user
               item.save()
             else:
                cart_item = CartItem.objects.filter(cart=cart)  
                for item in cart_item:
                  item.user = user
                  item.save()
      except:
        pass  
      auth.login(request, user)
      messages.success(request, 'You are logged in')
      url = request.META.get('HTTP_REFERER')
      try:
        query = requests.utils.urlparse(url).query
        #next=/carts/checkout
        params = dict(x.split('=') for x in query.split('&'))
        if 'next' in params:
            nextPage = params['next']
            return redirect(nextPage) 
      except: 
         return redirect('dashboard')  
      
    else:
      messages.error(request, 'Invalid login credentials')
      return redirect('login')
  return render(request, 'accounts/login.html')

@login_required(login_url='login')
def logout(request):
  auth.logout(request)
  messages.success(request, 'You Are Logged Out')
  return redirect('login')

def activate(request, uidb64, token):
  try:
     uid = urlsafe_base64_decode(uidb64).decode()
     user = Account._default_manager.get(pk=uid)
  except(TypeError, ValueError,OverflowError,Account.DoesNotExist):
    user = None 
  if user is not None and default_token_generator.check_token(user, token):
     user.is_active = True
     user.save()
     messages.success(request, 'Congratulations, your account has been activated')
     return redirect('login')
  else:
    messages.error(request, 'Invalid activation link') 
    return redirect('register') 
     
  
@login_required(login_url='login')  
def dashboard(request):
  return render(request, 'accounts/dashboard.html')
  

def forgotPassword(request):
  if request.method == 'POST':
    email = request.POST['email']
    if Account.objects.filter(email=email).exists():
      user = Account.objects.get(email__exact=email)
      
      #reset password
      current_site = get_current_site(request)
      mail_subject = 'Please Reset Your Password'
      message = render_to_string('accounts/reset_password_mail.html',{
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
      })
      to_email = email
      send_email = EmailMessage(mail_subject, message, to=[to_email])
      send_email.send()
      
      messages.success(request, 'Password reset mail has been sent to your email')
      return redirect('login')
      
    else:
      messages.error(request, 'Account does not exist')  
      return redirect('forgotPassword')
  return render(request, 'accounts/forgotpassword.html')


def passwordreset_validate(request, uidb64, token):
  try:
     uid = urlsafe_base64_decode(uidb64).decode()
     user = Account._default_manager.get(pk=uid)
  except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
    user = None
    
  if user is not None and default_token_generator.check_token(user, token): 
    request.session['uid'] = uid
    messages.success(request, 'Please reset your password')
    return redirect('resetPassword')
  else:
    messages.error(request, 'This link as expired')
    return redirect('login')
       
  return HttpResponse('ok')
  
def resetPassword(request):
  if request.method == 'POST':
    password = request.POST['password']
    confirm_password = request.POST['confirm_password']
    
    if password == confirm_password:
      uid = request.session.get('uid')
      user = Account.objects.get(pk=uid)
      user.set_password(password)
      user.save()
      messages.success(request, 'Password successfully reset')
      return redirect('login') 
    else:
      messages.error(request, 'Password does not match')
      return redirect('resetPassword') 
  else:   
    return render(request, 'accounts/resetPassword.html') 
  
  
  