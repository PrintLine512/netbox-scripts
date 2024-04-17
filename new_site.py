from django.utils.text import slugify

from dcim.choices import DeviceStatusChoices, SiteStatusChoices
from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from extras.scripts import *


class NewBranchScript(Script):

    class Meta:
        name = "Новый офис"
        description = "Добавить новый офис"
        #field_order = ['site_name', 'switch_count', 'switch_model']

    site_name = StringVar(
        description="Название офиса"
    )
    slug = StringVar(
        description="Имя латиницей, из спец. символов \"-\""
    )
    tenant = ObjectVar(
        model=Region
    )
    manufacturer_router = ObjectVar(
        model=Manufacturer,
        required=False
    )
    router_model = ObjectVar(
        description="Модель роутера",
        model=DeviceType,
        query_params={
            'manufacturer_id': '$manufacturer_router'
        }
    )
    manufacturer_switch = ObjectVar(
        model=Manufacturer,
        required=False
    )
    switch_model = ObjectVar(
        description="Модель свитча",
        model=DeviceType,
        query_params={
            'manufacturer_id': '$manufacturer_switch'
        }
    )
    switch_count = IntegerVar(
        description="Количество свитчей"
    )

    def run(self, data, commit):
        
        # Create the new site
        site = Site(
            name=data['site_name'],
            slug = data['slug'],
            tenant = data['tenant'],
            status=SiteStatusChoices.STATUS_PLANNED
        )
        site.full_clean()
        site.save()
        self.log_success(f"Created new site: {site}")

        # Create access switches
        switch_role = DeviceRole.objects.get(name='Access Switch')
        for i in range(1, data['switch_count'] + 1):
            switch = Device(
                device_type=data['switch_model'],
                name=f'{site.slug}-switch{i}',
                site=site,
                status=DeviceStatusChoices.STATUS_PLANNED,
                device_role=switch_role
            )
            switch.full_clean()
            switch.save()
            self.log_success(f"Created new switch: {switch}")

        # Generate a CSV table of new devices
        output = [
            'name,make,model'
        ]
        for switch in Device.objects.filter(site=site):
            attrs = [
                switch.name,
                switch.device_type.manufacturer.name,
                switch.device_type.model
            ]
            output.append(','.join(attrs))

        return '\n'.join(output)
