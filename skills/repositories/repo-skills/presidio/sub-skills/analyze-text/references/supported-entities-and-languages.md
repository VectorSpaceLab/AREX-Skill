# Supported entities and languages

## Inspect what is loaded

Useful runtime checks:

- `AnalyzerEngine.get_supported_entities(language=None)`
- `RecognizerRegistry.get_supported_entities(languages=None)`
- `RecognizerRegistry.get_country_codes()`

These reflect what is actually loaded in the current registry, not just what the
package can support in theory.

## Languages

Default analyzer behavior is English-first. Add or override languages through the
NLP engine and the registry together.

Common language rules:

- `supported_languages` can be a list of codes or a list of language/context objects
- the analyzer and registry must agree on the language set
- global context words only make sense when there is one language entry
- a country filter does not change language support; it only narrows country-tagged recognizers

Examples of valid language tags used in the source and tests:

- `en`
- `es`
- `it`
- `de`
- `pl`
- `fr-CA`
- `en-US`
- `en-GB`

## Global entities

Common locale-agnostic entities include:

- `CREDIT_CARD`
- `CRYPTO`
- `DATE_TIME`
- `EMAIL_ADDRESS`
- `IBAN_CODE`
- `IP_ADDRESS`
- `MAC_ADDRESS`
- `LOCATION`
- `ORGANIZATION` (common NER output)
- `PERSON`
- `PHONE_NUMBER`
- `NRP`
- `MEDICAL_LICENSE`
- `URL`
- `UUID`

## Country-specific entities

### United States

- `US_BANK_NUMBER`
- `US_DRIVER_LICENSE`
- `US_ITIN`
- `US_MBI`
- `US_NPI`
- `US_PASSPORT`
- `US_SSN`

### United Kingdom

- `UK_DRIVING_LICENCE`
- `UK_NHS`
- `UK_NINO`
- `UK_PASSPORT`
- `UK_POSTCODE`
- `UK_VEHICLE_REGISTRATION`

### Spain

- `ES_NIF`
- `ES_NIE`
- `ES_PASSPORT`

### Italy

- `IT_FISCAL_CODE`
- `IT_DRIVER_LICENSE`
- `IT_VAT_CODE`
- `IT_PASSPORT`
- `IT_IDENTITY_CARD`

### Poland

- `PL_PESEL`

### Singapore

- `SG_NRIC_FIN`
- `SG_UEN`

### Australia

- `AU_ABN`
- `AU_ACN`
- `AU_TFN`
- `AU_MEDICARE`

### India

- `IN_PAN`
- `IN_AADHAAR`
- `IN_VEHICLE_REGISTRATION`
- `IN_VOTER`
- `IN_PASSPORT`
- `IN_GSTIN`

### Finland

- `FI_PERSONAL_IDENTITY_CODE`

### Korea

- `KR_DRIVER_LICENSE`
- `KR_FRN`
- `KR_PASSPORT`
- `KR_BRN`
- `KR_RRN`

### Nigeria

- `NG_NIN`
- `NG_VEHICLE_REGISTRATION`

### Philippines

- `PH_PASSPORT`
- `PH_TIN`
- `PH_UMID`

### Canada

- `CA_SIN`
- `CA_POSTAL_CODE`

### Sweden

- `SE_ORGANISATIONSNUMMER`
- `SE_PERSONNUMMER`

### South Africa

- `ZA_ID_NUMBER`
- `ZA_PASSPORT`
- `ZA_INCOME_TAX_NUMBER`
- `ZA_DRIVER_LICENSE`
- `ZA_VAT_NUMBER`
- `ZA_COMPANY_REGISTRATION`
- `ZA_TRAFFIC_REGISTER_NUMBER`
- `ZA_LICENSE_PLATE`
- `ZA_MOBILE_NUMBER`
- `ZA_TELEPHONE_NUMBER`

### Thailand

- `TH_TNIN`

### Turkey

- `TR_NATIONAL_ID`
- `TR_LICENSE_PLATE`

### Germany

- `DE_TAX_ID`
- `DE_TAX_NUMBER`
- `DE_PASSPORT`
- `DE_ID_CARD`
- `DE_SOCIAL_SECURITY`
- `DE_HEALTH_INSURANCE`
- `DE_KFZ`
- `DE_HANDELSREGISTER`
- `DE_PLZ`

## Medical and clinical entities

These are available through the medical NER route and depend on the optional
transformers stack.

- `MEDICAL_DISEASE_DISORDER`
- `MEDICAL_MEDICATION`
- `MEDICAL_THERAPEUTIC_PROCEDURE`
- `MEDICAL_CLINICAL_EVENT`
- `MEDICAL_BIOLOGICAL_ATTRIBUTE`
- `MEDICAL_BIOLOGICAL_STRUCTURE`
- `MEDICAL_FAMILY_HISTORY`
- `MEDICAL_HISTORY`

## Model-based and third-party routes

GLiNER, LangExtract, Azure AI Language, and AHDS recognizers can emit their own
mapped Presidio entities depending on configuration. Common mapped outputs can
include `PERSON`, `LOCATION`, `ORGANIZATION`, `DATE_TIME`, `NRP`, `AGE`, `ID`,
`EMAIL`, and `PHONE_NUMBER`, but treat the exact set as configured output rather
than a fixed universal list.

## Practical notes

- `supported_countries=[]` keeps only locale-agnostic recognizers.
- `supported_countries=None` loads everything allowed by language and config.
- `AnalyzerEngine()` defaults to English unless you pass a different language set.
- Country-specific recognizers are filtered by country tags, not by text locale.
