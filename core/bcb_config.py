from __future__ import annotations

# Master definition of all BCB series we care about.
# Each entry: code -> dict with sgs_code, long_name, short_name
BCB_SERIES: dict[int, dict[str, str | int]] = {
    1: {
        "sgs_code": 1,
        "long_name": "BRL/USD Exchange Rate – End of period (commercial rate)",
        "short_name": "BRL/USD",
    },
    3546: {
        "sgs_code": 3546,
        "long_name": "International Reserves Total (US$ million, monthly)",
        "short_name": "Dollar Reserves",
    },
    22701: {
        "sgs_code": 22701,
        "long_name": "Current Account Balance (US$ million)",
        "short_name": "Current Account Balance",
    },
    23079: {
        "sgs_code": 23079,
        "long_name": "Current account accumulated in 12 months in relation to GDP - monthly (%)",
        "short_name": "CA accum. 12m/GDP",
    },
    4395: {
        "sgs_code": 4395,
        "long_name": "Future expectations index - Economic activity and price indicators",
        "short_name": "Future economic expectations index",
    },
    27815: {
        "sgs_code": 27815,
        "long_name": "Broad money supply - M4 (end-of-period balance)",
        "short_name": "M4 - Broad Money",
    },
    433: {
        "sgs_code": 433,
        "long_name": "IPCA",
        "short_name": "IPCA",
    },
    11: {
        "sgs_code": 11,
        "long_name": "Selic Diária",
        "short_name": "Selic diária",
    },
    1178: {
        "sgs_code": 1178,
        "long_name": "SELIC Policy Interest Rate (annualized, 252-day basis)",
        "short_name": "Selic (annual)",
    },
    256: {
        "sgs_code": 256,
        "long_name": "Taxa Juros Longo Prazo",
        "short_name": "Tx Juros LP",
    },
    4393: {
        "sgs_code": 4393,
        "long_name": "Consumer confidence index",
        "short_name": "Consum. confidence idx",
    },
    4380: {
        "sgs_code": 4380,
        "long_name": "GDP monthly - current prices",
        "short_name": "GDP monthly",
    },
    24363: {
        "sgs_code": 24363,
        "long_name": "IBC-BR Economic Activity Index",
        "short_name": "Economic Activity Index",
    },
    24371: {
        "sgs_code": 24371,
        "long_name": "Employed people in the private and public sector - PNADC",
        "short_name": "Employment (Pub+Priv)",
    },
    21859: {
        "sgs_code": 21859,
        "long_name": "General Industrial Output",
        "short_name": "Ind. Output",
    },
    1402: {
        "sgs_code": 1404,
        "long_name": "Industrial Electrical consumption GWh",
        "short_name": "Ind. Elec Cons.",
    },
    27574: {
        "sgs_code": 27574,
        "long_name": "Índice de Commodities - (IC-Br)",
        "short_name": "Ind Commodities",
    },
    27575: {
        "sgs_code": 27575,
        "long_name": "IC-Br - Agropecuária",
        "short_name": "IC-Br Agro",
    },
    27577: {
        "sgs_code": 27577,
        "long_name": "IC-Br - Energia",
        "short_name": "IC-Br Energy",
    },
    27576: {
        "sgs_code": 27576,
        "long_name": "IC-Br - Metal",
        "short_name": "IC-Br Metal",
    },
    4468: {
        "sgs_code": 4468,
        "long_name": "Net public debt - Balances in reais (million) - Total - Federal Government and Banco Central",
        "short_name": "Net public debt",
    },
    13762: {
        "sgs_code": 13762,
        "long_name": "Gross General Government Debt (% of GDP)",
        "short_name": "Gross debt/GDP",
    },
}

# Convenience mappings if you still want them:

# code -> long_name
BCB_LONG_BY_CODE: dict[int, str] = {
    code: meta["long_name"] for code, meta in BCB_SERIES.items()
}

# long_name -> short_name
BCB_SHORT_BY_LONG: dict[str, str] = {
    meta["long_name"]: meta["short_name"] for meta in BCB_SERIES.values()
}