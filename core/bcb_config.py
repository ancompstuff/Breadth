from __future__ import annotations

BCB_SGS_SERIES: dict[int, dict[str, str | int]] = {
    1: {
        'full_name': 'Exchange rate - Free - United States dollar (sale) - 1',
        'unit': 'c.m.u./US$',
        'periodicity': 'D',
        'start_date': '28/11/84',
        'source': 'Sisbacen PTAX800',
        'short_name': 'BRL/USD',
    },
    11: {
        'full_name': 'Interest rate - Selic',
        'unit': '% p.d.',
        'periodicity': 'D',
        'start_date': '04/06/86',
        'source': 'BCB-Demab',
        'short_name': 'Selic diária',
    },
    256: {
        'full_name': 'Long term interest rate (TJLP)',
        'unit': '% p.y.',
        'periodicity': 'M',
        'start_date': '01/12/94',
        'source': 'BCB-Demab',
        'short_name': 'Tx Juros LP',
    },
    433: {
        'full_name': 'Broad National Consumer Price Index (IPCA)',
        'unit': 'Monthly % var.',
        'periodicity': 'M',
        'start_date': '02/01/80',
        'source': 'IBGE',
        'short_name': 'IPCA',
    },
    1178: {
        'full_name': 'Interest rate - Selic in annual terms (basis 252)',
        'unit': '% p.y.',
        'periodicity': 'D',
        'start_date': '04/06/86',
        'source': 'BCB-Demab',
        'short_name': 'Selic (annual)',
    },
    1404: {
        'full_name': 'Electric energy consumption - Brazil - industrial',
        'unit': 'GWh',
        'periodicity': 'M',
        'start_date': '31/01/79',
        'source': 'Eletrobras',
        'short_name': 'Ind. Elec Consum',
    },
    3546: {
        'full_name': 'International reserves - Total - monthly',
        'unit': 'US$ (million)',
        'periodicity': 'M',
        'start_date': '31/12/70',
        'source': 'BCB-DSTAT',
        'short_name': 'Dollar Reserves',
    },
    4380: {
        'full_name': 'GDP monthly - current prices (R$ million)',
        'unit': 'R$ (million)',
        'periodicity': 'M',
        'start_date': '31/01/90',
        'source': 'BCB-Depec',
        'short_name': 'GDP monthly',
    },
    4393: {
        'full_name': 'Consumer confidence index',
        'unit': 'Index',
        'periodicity': 'M',
        'start_date': '31/03/99',
        'source': 'Fecomercio',
        'short_name': 'Consum. confidence',
    },
    4395: {
        'full_name': 'Future expectations index',
        'unit': 'Index',
        'periodicity': 'M',
        'start_date': '31/03/99',
        'source': 'Fecomercio',
        'short_name': 'Future economic exp',
    },
    4468: {
        'full_name': 'Net public debt - Balances in reais (million) - Total - Federal Government and Banco Central',
        'unit': 'R$ (million)',
        'periodicity': 'M',
        'start_date': '31/01/91',
        'source': 'BCB-DSTAT',
        'short_name': 'Net public debt',
    },
    13762: {
        'full_name': 'Gross general government debt (% GDP) - Method used since 2008',
        'unit': '%',
        'periodicity': 'M',
        'start_date': '01/12/06',
        'source': 'BCB-DSTAT',
        'short_name': 'Gross debt/GDP',
    },
    21859: {
        'full_name': 'General (2022=100)',
        'unit': 'Index',
        'periodicity': 'M',
        'start_date': '01/01/02',
        'source': 'IBGE',
        'short_name': 'Industrial Output',
    },
    22701: {
        'full_name': 'Current account - monthly - net',
        'unit': 'US$ (million)',
        'periodicity': 'M',
        'start_date': '01/01/95',
        'source': 'BCB-DSTAT',
        'short_name': 'Current Account Bal',
    },
    23079: {
        'full_name': 'Current account accumulated in 12 months in relation to GDP - monthly',
        'unit': '%',
        'periodicity': 'M',
        'start_date': '01/01/95',
        'source': 'BCB-DSTAT',
        'short_name': 'CA accum. Em 12m/GDP',
    },
    24363: {
        'full_name': 'Central Bank Economic Activity Index',
        'unit': 'Index',
        'periodicity': 'M',
        'start_date': '01/01/03',
        'source': 'BCB-Depec',
        'short_name': 'IBC-BR Econ Actvty',
    },
    24371: {
        'full_name': 'Employed people in the private and public sector - PNADC',
        'unit': 'Units (thousand)',
        'periodicity': 'M',
        'start_date': '01/03/12',
        'source': 'IBGE',
        'short_name': 'Employment (Pub+Priv)',
    },
    27574: {
        'full_name': 'Commodity Index - Brazil',
        'unit': 'Index',
        'periodicity': 'M',
        'start_date': '31/01/98',
        'source': 'BCB-Depec',
        'short_name': 'Idx Commodities',
    },
    27575: {
        'full_name': 'Commodity Index - Brazil - Agriculture',
        'unit': 'Index',
        'periodicity': 'M',
        'start_date': '31/01/98',
        'source': 'BCB-Depec',
        'short_name': 'IC-Br Agro',
    },
    27576: {
        'full_name': 'Commodity Index - Brazil - Metal',
        'unit': 'Index',
        'periodicity': 'M',
        'start_date': '31/01/98',
        'source': 'BCB-Depec',
        'short_name': 'IC-Br Metal',
    },
    27577: {
        'full_name': 'Commodity Index - Brazil - Energy',
        'unit': 'Index',
        'periodicity': 'M',
        'start_date': '31/01/98',
        'source': 'BCB-Depec',
        'short_name': 'IC-Br Energy',
    },
    27815: {
        'full_name': 'Broad money supply - M4 (end-of-period balance) - New',
        'unit': 'c.m.u. (thousand)',
        'periodicity': 'M',
        'start_date': '01/12/01',
        'source': 'BCB-DSTAT',
        'short_name': 'M4 - Broad Money',
    },
}

# long_name -> short_name
BCB_SHORT_BY_LONG: dict[str, str] = {
    meta["full_name"]: meta["short_name"] for meta in BCB_SGS_SERIES.values()
}

"""# Convenience mappings if you still want them:

# code -> long_name
BCB_LONG_BY_CODE: dict[int, str] = {
    code: meta["full_name"] for code, meta in BCB_SGS_SERIES.items()
}



# SGS datasets that still use legacy padded numeric formatting
LEGACY_SGS = {11, 1178}"""