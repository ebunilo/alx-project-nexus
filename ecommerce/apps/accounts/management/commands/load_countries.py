"""
Management command to load and sync country reference data.

This command uses the pycountry library to populate the Country model
with ISO 3166-1 country data. It is idempotent and treats country data
as reference/master data.

Usage:
    python manage.py load_countries
    python manage.py load_countries --dry-run
    python manage.py load_countries --deactivate-missing
    python manage.py load_countries --only-common

Note: --only-common controls which countries are created/updated.
      --deactivate-missing always uses the FULL pycountry set to determine
      which countries are invalid, so these flags can be safely combined.
"""

from typing import Dict, Any

import pycountry
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from apps.accounts.models import Country


# Mapping of country codes to phone codes (pycountry doesn't include these)
# This is a subset of common countries; extend as needed
PHONE_CODES: Dict[str, str] = {
    'AF': '+93', 'AL': '+355', 'DZ': '+213', 'AD': '+376', 'AO': '+244',
    'AR': '+54', 'AM': '+374', 'AU': '+61', 'AT': '+43', 'AZ': '+994',
    'BH': '+973', 'BD': '+880', 'BY': '+375', 'BE': '+32', 'BJ': '+229',
    'BT': '+975', 'BO': '+591', 'BA': '+387', 'BW': '+267', 'BR': '+55',
    'BN': '+673', 'BG': '+359', 'BF': '+226', 'BI': '+257', 'KH': '+855',
    'CM': '+237', 'CA': '+1', 'CV': '+238', 'CF': '+236', 'TD': '+235',
    'CL': '+56', 'CN': '+86', 'CO': '+57', 'KM': '+269', 'CG': '+242',
    'CD': '+243', 'CR': '+506', 'CI': '+225', 'HR': '+385', 'CU': '+53',
    'CY': '+357', 'CZ': '+420', 'DK': '+45', 'DJ': '+253', 'DO': '+1',
    'EC': '+593', 'EG': '+20', 'SV': '+503', 'GQ': '+240', 'ER': '+291',
    'EE': '+372', 'SZ': '+268', 'ET': '+251', 'FJ': '+679', 'FI': '+358',
    'FR': '+33', 'GA': '+241', 'GM': '+220', 'GE': '+995', 'DE': '+49',
    'GH': '+233', 'GR': '+30', 'GT': '+502', 'GN': '+224', 'GW': '+245',
    'GY': '+592', 'HT': '+509', 'HN': '+504', 'HK': '+852', 'HU': '+36',
    'IS': '+354', 'IN': '+91', 'ID': '+62', 'IR': '+98', 'IQ': '+964',
    'IE': '+353', 'IL': '+972', 'IT': '+39', 'JM': '+1', 'JP': '+81',
    'JO': '+962', 'KZ': '+7', 'KE': '+254', 'KW': '+965', 'KG': '+996',
    'LA': '+856', 'LV': '+371', 'LB': '+961', 'LS': '+266', 'LR': '+231',
    'LY': '+218', 'LI': '+423', 'LT': '+370', 'LU': '+352', 'MG': '+261',
    'MW': '+265', 'MY': '+60', 'MV': '+960', 'ML': '+223', 'MT': '+356',
    'MR': '+222', 'MU': '+230', 'MX': '+52', 'MD': '+373', 'MC': '+377',
    'MN': '+976', 'ME': '+382', 'MA': '+212', 'MZ': '+258', 'MM': '+95',
    'NA': '+264', 'NP': '+977', 'NL': '+31', 'NZ': '+64', 'NI': '+505',
    'NE': '+227', 'NG': '+234', 'KP': '+850', 'MK': '+389', 'NO': '+47',
    'OM': '+968', 'PK': '+92', 'PA': '+507', 'PG': '+675', 'PY': '+595',
    'PE': '+51', 'PH': '+63', 'PL': '+48', 'PT': '+351', 'QA': '+974',
    'RO': '+40', 'RU': '+7', 'RW': '+250', 'SA': '+966', 'SN': '+221',
    'RS': '+381', 'SL': '+232', 'SG': '+65', 'SK': '+421', 'SI': '+386',
    'SO': '+252', 'ZA': '+27', 'KR': '+82', 'SS': '+211', 'ES': '+34',
    'LK': '+94', 'SD': '+249', 'SR': '+597', 'SE': '+46', 'CH': '+41',
    'SY': '+963', 'TW': '+886', 'TJ': '+992', 'TZ': '+255', 'TH': '+66',
    'TL': '+670', 'TG': '+228', 'TT': '+1', 'TN': '+216', 'TR': '+90',
    'TM': '+993', 'UG': '+256', 'UA': '+380', 'AE': '+971', 'GB': '+44',
    'US': '+1', 'UY': '+598', 'UZ': '+998', 'VE': '+58', 'VN': '+84',
    'YE': '+967', 'ZM': '+260', 'ZW': '+263',
}

# Mapping of country codes to currency codes
# pycountry has this but it's in a separate module
CURRENCY_CODES: Dict[str, str] = {
    'AF': 'AFN', 'AL': 'ALL', 'DZ': 'DZD', 'AD': 'EUR', 'AO': 'AOA',
    'AR': 'ARS', 'AM': 'AMD', 'AU': 'AUD', 'AT': 'EUR', 'AZ': 'AZN',
    'BH': 'BHD', 'BD': 'BDT', 'BY': 'BYN', 'BE': 'EUR', 'BJ': 'XOF',
    'BT': 'BTN', 'BO': 'BOB', 'BA': 'BAM', 'BW': 'BWP', 'BR': 'BRL',
    'BN': 'BND', 'BG': 'BGN', 'BF': 'XOF', 'BI': 'BIF', 'KH': 'KHR',
    'CM': 'XAF', 'CA': 'CAD', 'CV': 'CVE', 'CF': 'XAF', 'TD': 'XAF',
    'CL': 'CLP', 'CN': 'CNY', 'CO': 'COP', 'KM': 'KMF', 'CG': 'XAF',
    'CD': 'CDF', 'CR': 'CRC', 'CI': 'XOF', 'HR': 'EUR', 'CU': 'CUP',
    'CY': 'EUR', 'CZ': 'CZK', 'DK': 'DKK', 'DJ': 'DJF', 'DO': 'DOP',
    'EC': 'USD', 'EG': 'EGP', 'SV': 'USD', 'GQ': 'XAF', 'ER': 'ERN',
    'EE': 'EUR', 'SZ': 'SZL', 'ET': 'ETB', 'FJ': 'FJD', 'FI': 'EUR',
    'FR': 'EUR', 'GA': 'XAF', 'GM': 'GMD', 'GE': 'GEL', 'DE': 'EUR',
    'GH': 'GHS', 'GR': 'EUR', 'GT': 'GTQ', 'GN': 'GNF', 'GW': 'XOF',
    'GY': 'GYD', 'HT': 'HTG', 'HN': 'HNL', 'HK': 'HKD', 'HU': 'HUF',
    'IS': 'ISK', 'IN': 'INR', 'ID': 'IDR', 'IR': 'IRR', 'IQ': 'IQD',
    'IE': 'EUR', 'IL': 'ILS', 'IT': 'EUR', 'JM': 'JMD', 'JP': 'JPY',
    'JO': 'JOD', 'KZ': 'KZT', 'KE': 'KES', 'KW': 'KWD', 'KG': 'KGS',
    'LA': 'LAK', 'LV': 'EUR', 'LB': 'LBP', 'LS': 'LSL', 'LR': 'LRD',
    'LY': 'LYD', 'LI': 'CHF', 'LT': 'EUR', 'LU': 'EUR', 'MG': 'MGA',
    'MW': 'MWK', 'MY': 'MYR', 'MV': 'MVR', 'ML': 'XOF', 'MT': 'EUR',
    'MR': 'MRU', 'MU': 'MUR', 'MX': 'MXN', 'MD': 'MDL', 'MC': 'EUR',
    'MN': 'MNT', 'ME': 'EUR', 'MA': 'MAD', 'MZ': 'MZN', 'MM': 'MMK',
    'NA': 'NAD', 'NP': 'NPR', 'NL': 'EUR', 'NZ': 'NZD', 'NI': 'NIO',
    'NE': 'XOF', 'NG': 'NGN', 'KP': 'KPW', 'MK': 'MKD', 'NO': 'NOK',
    'OM': 'OMR', 'PK': 'PKR', 'PA': 'PAB', 'PG': 'PGK', 'PY': 'PYG',
    'PE': 'PEN', 'PH': 'PHP', 'PL': 'PLN', 'PT': 'EUR', 'QA': 'QAR',
    'RO': 'RON', 'RU': 'RUB', 'RW': 'RWF', 'SA': 'SAR', 'SN': 'XOF',
    'RS': 'RSD', 'SL': 'SLE', 'SG': 'SGD', 'SK': 'EUR', 'SI': 'EUR',
    'SO': 'SOS', 'ZA': 'ZAR', 'KR': 'KRW', 'SS': 'SSP', 'ES': 'EUR',
    'LK': 'LKR', 'SD': 'SDG', 'SR': 'SRD', 'SE': 'SEK', 'CH': 'CHF',
    'SY': 'SYP', 'TW': 'TWD', 'TJ': 'TJS', 'TZ': 'TZS', 'TH': 'THB',
    'TL': 'USD', 'TG': 'XOF', 'TT': 'TTD', 'TN': 'TND', 'TR': 'TRY',
    'TM': 'TMT', 'UG': 'UGX', 'UA': 'UAH', 'AE': 'AED', 'GB': 'GBP',
    'US': 'USD', 'UY': 'UYU', 'UZ': 'UZS', 'VE': 'VES', 'VN': 'VND',
    'YE': 'YER', 'ZM': 'ZMW', 'ZW': 'ZWL',
}


class Command(BaseCommand):
    """
    Management command to load and sync country reference data.

    This command is idempotent - it can be run multiple times safely.
    It will create new countries, update existing ones, and optionally
    deactivate countries that are no longer in the pycountry database.
    """

    help = 'Load and sync country reference data from pycountry library'

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Add command line arguments.

        Args:
            parser (CommandParser): The argument parser.
        """
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--deactivate-missing',
            action='store_true',
            help='Deactivate countries not found in pycountry',
        )
        parser.add_argument(
            '--only-common',
            action='store_true',
            help='Only load common countries (those with phone codes defined)',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Execute the command.

        Args:
            *args: Variable length argument list.
            **options: Keyword arguments from command line.
        """
        dry_run = options['dry_run']
        deactivate_missing = options['deactivate_missing']
        only_common = options['only_common']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))

        created_count = 0
        updated_count = 0
        unchanged_count = 0
        deactivated_count = 0

        # Build the full set of pycountry codes (used for deactivate-missing)
        # This must be computed from ALL pycountry entries, not filtered by
        # --only-common, to avoid accidentally deactivating valid countries.
        all_pycountry_codes = {c.alpha_2 for c in pycountry.countries}

        with transaction.atomic():
            for country in pycountry.countries:
                code = country.alpha_2

                # Skip if only_common and no phone code defined
                if only_common and code not in PHONE_CODES:
                    continue

                country_data = {
                    'name': country.name,
                    'phone_code': PHONE_CODES.get(code, ''),
                    'currency_code': CURRENCY_CODES.get(code, ''),
                    'is_active': True,
                }

                try:
                    existing = Country.objects.get(code=code)
                    # Check if update needed
                    needs_update = (
                        existing.name != country_data['name'] or
                        existing.phone_code != country_data['phone_code'] or
                        existing.currency_code != country_data['currency_code'] or
                        not existing.is_active
                    )

                    if needs_update:
                        if not dry_run:
                            for key, value in country_data.items():
                                setattr(existing, key, value)
                            existing.save()
                        updated_count += 1
                        self.stdout.write(
                            f"  Updated: {code} - {country_data['name']}"
                        )
                    else:
                        unchanged_count += 1

                except Country.DoesNotExist:
                    if not dry_run:
                        Country.objects.create(code=code, **country_data)
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Created: {code} - {country_data['name']}"
                        )
                    )

            # Deactivate countries not in pycountry (using full set, not filtered)
            if deactivate_missing:
                existing_codes = set(
                    Country.objects.filter(is_active=True)
                    .values_list('code', flat=True)
                )
                missing_codes = existing_codes - all_pycountry_codes

                for code in missing_codes:
                    if not dry_run:
                        Country.objects.filter(code=code).update(is_active=False)
                    deactivated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  Deactivated: {code}")
                    )

            if dry_run:
                # Rollback transaction for dry run
                transaction.set_rollback(True)

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('Country data sync complete'))
        self.stdout.write(f"  Created:     {created_count}")
        self.stdout.write(f"  Updated:     {updated_count}")
        self.stdout.write(f"  Unchanged:   {unchanged_count}")
        if deactivate_missing:
            self.stdout.write(f"  Deactivated: {deactivated_count}")
        self.stdout.write(self.style.SUCCESS('='*50))
