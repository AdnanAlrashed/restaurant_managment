import time
import os
import traceback
import datetime
import json


from django.core.exceptions import ObjectDoesNotExist
from django.forms import modelformset_factory
from django.db.models import IntegerField
from django.db.models.functions import Cast



from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse,  HttpResponse, QueryDict
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.db.models import Max
from django.shortcuts import render, redirect, get_object_or_404
from django.core import serializers
from django.db import transaction, IntegrityError
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, CreateView, View, UpdateView, DeleteView
from django.urls import reverse
from django.db.models import Q, F
from django.conf import settings
from django.utils.html import format_html
from configrate.models import Unit,Store
from input.models import Items




from purchases.forms import (
    PurchaseInvoiceForm,
    PurchaseInvoicelocalDetailsForm,
    
)
from purchases.models import (
    PurchaseInvoicelocal,
    PurchaseInvoicelocalDetails,
)
from purchases.Supplier.forms import SupplierForm
from purchases.models import  Supplier

class PurchaseInvoice(CreateView):
    def get(self, request, *args, **kwargs):
        result = {"status": 0, "message": ""}

        if "id" in request.GET.keys():

            if request.GET.get("id"):
                formdata = PurchaseInvoicelocal.objects.filter(
                    pk=int(request.GET.get("id"))
                )
         
                supplierdata1 = Supplier.objects.values("id", "arabic_name").get(
                    pk=formdata[0].supplir_id
                )
                supplierdata = {
                    "id": supplierdata1["id"],
                    "name": supplierdata1["arabic_name"],
                }

                formsetdata = PurchaseInvoicelocalDetails.objects.filter(
                    purchase_invoicelocal_id=int(request.GET.get("id"))
                )

                listdata = []

                for i in formsetdata:
                    d = Item.objects.values("id", "name_ar", "name_en").get(
                        pk=i.item_id
                    )
                    listdata.append(d)

                # data_item =

                result = {
                    "status": 1,
                    "datasupplier": supplierdata,
                    "dataitem": listdata,
                    "data1": serializers.serialize("json", formdata),
                    "data2": serializers.serialize("json", formsetdata),
                }

                # except:
                # result={'status':0,'data':"not found"}

                return JsonResponse(result)

        else:
  
            try:

                DataFormset = modelformset_factory(
                    PurchaseInvoicelocalDetails, form=PurchaseInvoicelocalDetailsForm
                )
                formset = DataFormset(
                    request.GET or None,
                    queryset=PurchaseInvoicelocalDetails.objects.none(),
                    prefix="PurchaseInvoicelocalDetails",
                )
                db_years_name=0
                

                form1 = PurchaseInvoiceForm()

                context = {
                    "Variable":{
                        "is_expire_date":1
                        },
                    "form": form1,
                    "formset": formset,
                    "url": reverse("PurchaseInvoice"),
                    "title_list": _("Purchase Invoice local"),
                    "dialog_form1": SupplierForm(),
                    # "url_dialog_form1": reverse("SupplierView"),
                    "dialog_form_title1": _("Add Supplier "),
                    # "dialog_form2": StoreForm(),
                    # "url_dialog_form2": reverse("StoreView"),
                    "dialog_form_title2": _("Add Store "),
                }
            except ObjectDoesNotExist as e:

                data = _("Error must initial GeneralVariables in app supplier")

                result = {
                    "status": 0,
                    "message": {"message": data, "class": "alert alert-danger"},
                }
                # return JsonResponse(result)
                context = {
                    "error": data,
                }
            return render(request, "purchases/purchases/purchase_invoicelocal.html", context)

    def post(self, request, *args, **kwargs):
        result = {"status": 0, "class": "","message": ""}
        is_note=None
        is_expire_date = None    
        db_years_name=0
        db_years_name=2023
        Variable={
                "is_note":is_note,
                'is_expire_date':is_expire_date,
                "years_date":db_years_name,

            }
        form = PurchaseInvoiceForm(request.POST)
        DataFormset = modelformset_factory(
            PurchaseInvoicelocalDetails, form=PurchaseInvoicelocalDetailsForm
        )
        formset = DataFormset(
            request.POST or None,
            queryset=PurchaseInvoicelocalDetails.objects.none(),
            prefix="PurchaseInvoicelocalDetails",
        )

        result = {"status": 0, "message": ""}

        if request.POST.get("id_invoice"):
           
            try:
                pk_ivoice = int(request.POST["id_invoice"])
                data_form = get_object_or_404(
                    PurchaseInvoicelocal, pk=int(request.POST["id_invoice"])
                )
                obj_edit = PurchaseInvoicelocal.objects.get(pk=pk_ivoice)

                Variable={
                    "is_cost_center":is_cost_center,
                    "is_note":is_note,
                    'is_expire_date':is_expire_date,
                    "years_date":db_years_name

                }
                form = PurchaseInvoiceForm(request.POST, instance=data_form)

                formset = DataFormset(
                    request.POST,
                    queryset=PurchaseInvoicelocalDetails.objects.none(),
                    prefix="PurchaseInvoicelocalDetails",
                )
                if data_form.is_editable() == False:
                    msg = _(
                        "Error ! The invoice has been deported or movement in item and cannot be modified"
                    )

                    raise InvoiceExcept(msg)
            except InvoiceExcept as e:
                traceback.print_exc()
                result["status"] = 3
                result["message"] = {
                    "message": str(e),
                    "class": "alert alert-danger",
                }
                return JsonResponse(result)
            except Exception as e:
                traceback.print_exc()

                msg = _("inexcpected error has been ocred")
                result = {"status": 3, "message": msg}
                return JsonResponse(result)


        if form.is_valid() and formset.is_valid():

            try:
               
                if request.POST.get("id_invoice"):
                    obj_edit.before_edite(request)
                obj = form.save(commit=False)
                if request.POST.get("id_invoice"):
                    obj.modified_by_id = request.user.id
                else:
                    obj.created_by_id = request.user.id
                
                if not request.POST.get("id_invoice"):
                    obj.code = get_maxcode()
                obj.save()
                if formset.is_valid():
                    details_obj = formset.save(commit=False)

                    for instance in details_obj:

                        instance.purchase_invoicelocal_id = obj.id
                        instance.save()
                doc_id = 0
                if request.POST.get("id_invoice"):
                    msg = "تم التعديل بنجاح"
                    result = {"status": 1, "message": msg}
                else:
                    msg = "تم الحفظ بنجاح"
                    result = {"status": 1, "message": msg}
            except IntegrityError as e:

                traceback.print_exc()

                result["status"] = 3
                result["message"] = {
                    "message": str(e),
                    "class": "alert alert-danger",
                }
                return JsonResponse(result)
            except ObjectDoesNotExist as e:
                traceback.print_exc()

                msg = str(e)
                result = {"status": 3, "message": msg, "msg": _("error")}

            except Exception as e:
                traceback.print_exc()
                msg = _("inexcpacted error")
                result = {"status": 3, "message": msg, "msg": _("error")}

        else:
            if not formset.is_valid():

                row = 0
                for f in formset.forms:
                    if not f.is_valid():
                        result = {
                            "status": 0,
                            "error": "",
                            "error2": f.errors.as_json(),
                            "row": row,
                        }
                        break
                    row = row + 1

            else:
             
                result = {"status": 0, "error": form.errors}

        return JsonResponse(result)

    def delete(self, request, *args, **kwargs):
        result = {"status": 0, "message": ""}

        pk = int(QueryDict(request.body).get("id"))
        if pk:
            try:
                with transaction.atomic(using=request.session.get("db_name")):
                    data = get_object_or_404(PurchaseInvoicelocal, pk=pk)

                    data.delete()
                    msg = "تم الحذف بنجاح"
                    result = {"status": 1, "message": msg}
            except InvoiceExcept as e:
                result["status"] = 3
                result["message"] = {
                    "message": str(e),
                    "class": "alert alert-danger",
                }
                return JsonResponse(result)
            except Exception as e:
                msg = str(e)
                result = {"status": 3, "message": msg, "msg": _("error")}
        else:
            msg = "خطاء بالحذف"
            result = {"status": 0, "message": msg}
        return JsonResponse(result)


def get_code(request):
  
    new_code = get_maxcode()
    data = {"status": 1, "data": new_code}
    return JsonResponse(data)

def get_maxcode():
    
    code=PurchaseInvoicelocal.objects.all().annotate(code1=Cast(F('code'),output_field=IntegerField())).aggregate(id_max=Max((("code1")),output_field=IntegerField()))
    
    number_max = next(iter(code.values()))
    if number_max != None:
        new_code = int(number_max) + 1
    else:
        new_code = "1"
    return new_code


class PurchaseListJson(BaseDatatableView):
    model = PurchaseInvoicelocal
    columns = [
        
        "code",
        "date",
        "supplir__name_lo",
        "total_amount",
        "action"
    ]

    order_columns = [
        "code",
        "date",
        "supplir__name_lo",
        "total_amount",
        "action",
    ]

    def get_initial_queryset(self):
        return self.model.objects.values(
            "id",
            "code",
            "date",
            "supplir__name_lo",
            "total_amount",
        ).filter(stop=False)

    count = 0

    def render_column(self, row, column):
        if column == "#":
            self.count += 1
            return str(self.count)
        elif column == "action":
            return '<a class="edit_row" data-url="{3}" data-id="{0}" style="DISPLAY: ' \
                   '-webkit-inline-box;margin-right:5px;"  data-toggle="tooltip" title="{1}"><i class="fa ' \
                   'fa-edit"></i></a><a class="delete_row" data-url="{3}" data-id="{0}"  style="DISPLAY: ' \
                   '-webkit-inline-box;margin-right:5px;" data-toggle="tooltip" title="{2}"><i class="fa ' \
                   'fa-trash"></i></a>'.format(
                row['id'], _("تعديل"), _("حذف"), reverse("PurchaseInvoice"))
        else:
            return super(PurchaseListJson, self).render_column(row, column)

    def filter_queryset(self, qs):
        """To Filter data in table using in search
        """
        sSearch = self.request.GET.get("sSearch", None)
        if sSearch:
            qs = qs.filter(
                Q(id__icontains=sSearch)
                | Q(code__icontains=sSearch)
            )
        return qs