from rest_framework import generics, status, views, mixins
from django.contrib.auth.models import User
from rest_framework.response import Response
from lib.utility import Utility
from core.models import MessageQueue, RestrictedItems, Vehicle, CompanyDepartments, CompanyEntranceNames, UserProfile
from api.permissions import *
from api.v1.core.serializers import CompanyDepartmentsSerializer, VehicleSerializer, CompanyEntranceNamesSerializer,\
    RestrictedItemsSerializer


class SendEmail(views.APIView):

    def post(self, request):
        errors = []

        subject = request.DATA.get('subject')
        email = request.DATA.get('email')
        message = request.DATA.get('message')
        if subject is None:
            errors.append('please provide mail subject')

        if message is None:
            errors.append('please provide mail message')

        if email is None:
            errors.append('please provide mail address')

        if len(errors):
            return Response({'error_message': ', '.join(errors)}, status=status.HTTP_400_BAD_REQUEST)

        mail_response = Utility.send_email(subject, message, [email])
        if mail_response:
            return Response({'error_message': '', 'message': 'message sent successfully'})
        queue = MessageQueue(
            destination=email,
            message_body=message,
            subject=subject,
            type=0
        )
        queue.save()
        return Response({'error_message': '', 'message': 'message was queued to be sent'})


class VehicleList(generics.ListAPIView, mixins.CreateModelMixin):

    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class VehicleDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                    generics.GenericAPIView, mixins.CreateModelMixin):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    lookup_field = 'uuid'

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class RestrictedItemsList(generics.ListAPIView, mixins.CreateModelMixin):

    queryset = RestrictedItems.objects.all()
    serializer_class = RestrictedItemsSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class RestrictedItemsDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                            generics.GenericAPIView, mixins.CreateModelMixin):
    queryset = RestrictedItems.objects.all()
    serializer_class = RestrictedItemsSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    lookup_field = 'uuid'

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class CompanyDepartmentsList(generics.ListAPIView, mixins.CreateModelMixin):

    queryset = CompanyDepartments.objects.all()
    serializer_class = CompanyDepartmentsSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class CompanyDepartmentsDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                               generics.GenericAPIView, mixins.CreateModelMixin):
    queryset = CompanyDepartments.objects.all()
    serializer_class = CompanyDepartmentsSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    lookup_field = 'uuid'

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class CompanyEntranceNamesList(generics.ListAPIView, mixins.CreateModelMixin):

    queryset = CompanyEntranceNames.objects.all()
    serializer_class = CompanyEntranceNamesSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class CompanyEntranceNamesDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                                 generics.GenericAPIView, mixins.CreateModelMixin):
    queryset = CompanyEntranceNames.objects.all()
    serializer_class = CompanyEntranceNamesSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    lookup_field = 'uuid'

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token
import ldap
import os
import json
from core.settings import PROJECT_ROOT

def loadConfig():
    file_name = os.path.join(PROJECT_ROOT, 'ldap.json')
    data = {}
    if os.path.isfile(file_name):
        file = open(file_name)
        data = file.read()
        return json.loads(data)
    return data


def get_or_create_user(user, username=None, password=None):
    import time
    ts = '{}'.format(time.time()).split('.')

    if len(user) > 0:
        cn, user = user[0]
        if username is None:
            username = user.get('sAMAccountName', None)
        if password is None:
            password = 'password@1'

        fullname = user['displayName'][0].split(' ')
        first_name = fullname[0]
        last_name = 'None'
        user_email = user.get('mail', None)
        phone = user.get('telephoneNumber', None)
        department_info = user.get('distinguishedName', None)

        if len(fullname) > 1:
                last_name = fullname[1]

        if phone is not None:
            phone = phone[0]
        else:
            phone = ts[0]

        if user_email is not None:
            user_email = user_email[0]
        else:
            user_email = 'mail{0}@ncc.org'.format(ts[0])

        if department_info is not None:
            department_info = department_info[0].split(',')
            department_info = department_info[1].split('=')
            department_info = department_info[1]
        else:
            department_info = 'None'

        try:
            user_instance = User.objects.get(username=username)
            user_instance.first_name = first_name
            user_instance.last_name = last_name
            user_instance.email = user_email
            user_instance.save()

            UserProfile(
                user_id=User.objects.get(username=username),
                phone=phone,
                department=department_info
            ).save()

            return user_instance
        except User.DoesNotExist:

            user_instance = User.objects.get_or_create(
                username=username,
                password=password,
                email=user_email,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )

            UserProfile(
                user_id=User.objects.get(username=username),
                phone=phone,
                department=department_info
            ).save()

            return user_instance
    else:
        return None


def ldap_login(username, password):

    ldap_settings = loadConfig()
    server_name = ldap_settings.get('serverName', '172.16.0.21')
    port = ldap_settings.get('port', 389)
    domain_controller = ldap_settings.get('domainController', 'ncc.local')
    dn = domain_controller.split('.')
    dc = []
    for ns in dn:
        dc.append('dc={}'.format(ns))

    dn = ','.join(dc)

    l = ldap.initialize("ldap://{0}:{1}".format(server_name, port))
        # Bind/authenticate with a user with apropriate rights to add objects
    l.protocol_version = ldap.VERSION3
    l.set_option(ldap.OPT_REFERRALS, 0)
    bind_dn  = "ncc\\{0}".format(username)
    dn_password = password
    l.simple_bind_s(bind_dn, password)

    # The dn of our new entry/object

    user = l.search_ext_s(dn, ldap.SCOPE_SUBTREE, "(sAMAccountName="+username+")",
                          attrlist=["sAMAccountName", "displayName","mail", "distinguishedName", "telephoneNumber"])

    return get_or_create_user(user, username, password)


class ImportUsersFromLDAP(views.APIView):

    def get(self, request):

        ldap_settings = loadConfig()
        server_name = ldap_settings.get('serverName', '192.168.1.100')
        port = ldap_settings.get('port', 389)
        admin_username = ldap_settings.get('adminUsername', 'administrator')
        bind_password = ldap_settings.get('bindPassword', '')
        domain_controller = ldap_settings.get('domainController', 'vms')
        dn = domain_controller.split('.')
        dc = []
        for ns in dn:
            dc.append('dc={}'.format(ns))

        dn = ','.join(dc)

        try:
            # Open a connection
            l = ldap.initialize("ldap://{0}:{1}".format(server_name, port))
            # Bind/authenticate with a user with apropriate rights to add objects
            l.protocol_version = ldap.VERSION3
            l.set_option(ldap.OPT_REFERRALS, 0)
            bind_dn  = "{0}\\{1}".format(dn[0], admin_username)
            l.simple_bind_s(bind_dn, bind_password)

            # The dn of our new entry/object


            users = l.search_ext_s(dn, ldap.SCOPE_SUBTREE, "(telephoneNumber=*)",
                          attrlist=["sAMAccountName", "displayName","mail", "distinguishedName", "telephoneNumber"])

            for cn, user in users:
                get_or_create_user(user)

            return Response({'detail': ''})
        except ldap.LDAPError, e:

            return Response({'detail': e}, status.HTTP_400_BAD_REQUEST)


class TestConnection(views.APIView):

    def post(self, request):

        ldap_settings = request.DATA
        server_name = ldap_settings.get('serverName', '172.16.0.21')
        port = ldap_settings.get('port', 389)
        admin_username = ldap_settings.get('adminUsername', 'administrator')
        bind_password = ldap_settings.get('bindPassword', '')
        domain_controller = ldap_settings.get('domainController', 'ncc.local')
        dn = domain_controller.split('.')
        dc = []
        for ns in dn:
            dc.append('dc={}'.format(ns))

        dn = ','.join(dc)

        try:
            # Open a connection
            l = ldap.initialize("ldap://{0}:{1}".format(server_name, port))
            # Bind/authenticate with a user with apropriate rights to add objects
            l.protocol_version = ldap.VERSION3
            l.set_option(ldap.OPT_REFERRALS, 0)
            bind_dn  = "ncc\\{0}".format(admin_username)
            l.simple_bind_s(bind_dn, bind_password)

            # The dn of our new entry/object
            dn=dc

            user = l.search_ext_s(dn, ldap.SCOPE_SUBTREE, "(sAMAccountName="+admin_username+")",
            attrlist=["sAMAccountName", "displayName","mail"])
            return Response()
        except:
            return Response({'detail': 'Problem with ldap connection'})


class AuthUser(views.APIView):

    def post(self, request):

        username = request.DATA.get('username', None)
        password = request.DATA.get('password', None)
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                token = Token.objects.get(user=user)
                return Response({'token': token.key})
            else:
                return Response({'detail': 'User not active'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            ldap_user = ldap_login(username, password)
            if ldap_user is not None:
                token = Token.objects.get(user=ldap_user)
                return Response({'token': token.key})

            return Response({'detail': 'invalid credentials provided'}, status=status.HTTP_400_BAD_REQUEST)
            # Return an 'invalid login' error message.

        #return Response({'error_message': '',DATA 'message': request.DATA})