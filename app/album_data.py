TEAM_GROUPS = [
    {
        "grupo": "A",
        "cor": "Verde",
        "selecoes": [
            {"sigla": "MEX", "nome": "Mexico"},
            {"sigla": "RSA", "nome": "South Africa"},
            {"sigla": "KOR", "nome": "Korea Republic"},
            {"sigla": "CZE", "nome": "Czechia"},
        ],
    },
    {
        "grupo": "B",
        "cor": "Vermelho",
        "selecoes": [
            {"sigla": "CAN", "nome": "Canada"},
            {"sigla": "BIH", "nome": "Bosnia-Herzegovina"},
            {"sigla": "QAT", "nome": "Qatar"},
            {"sigla": "SUI", "nome": "Switzerland"},
        ],
    },
    {
        "grupo": "C",
        "cor": "Amarelo",
        "selecoes": [
            {"sigla": "BRA", "nome": "Brazil"},
            {"sigla": "MAR", "nome": "Morocco"},
            {"sigla": "HAI", "nome": "Haiti"},
            {"sigla": "SCO", "nome": "Scotland"},
        ],
    },
    {
        "grupo": "D",
        "cor": "Azul",
        "selecoes": [
            {"sigla": "USA", "nome": "USA"},
            {"sigla": "PAR", "nome": "Paraguay"},
            {"sigla": "AUS", "nome": "Australia"},
            {"sigla": "TUR", "nome": "Türkiye"},
        ],
    },
    {
        "grupo": "E",
        "cor": "Laranja",
        "selecoes": [
            {"sigla": "GER", "nome": "Germany"},
            {"sigla": "CUW", "nome": "Curaçao"},
            {"sigla": "CIV", "nome": "Côte d'Ivoire"},
            {"sigla": "ECU", "nome": "Ecuador"},
        ],
    },
    {
        "grupo": "F",
        "cor": "Verde Escuro",
        "selecoes": [
            {"sigla": "NED", "nome": "Netherlands"},
            {"sigla": "JPN", "nome": "Japan"},
            {"sigla": "SWE", "nome": "Sweden"},
            {"sigla": "TUN", "nome": "Tunisia"},
        ],
    },
    {
        "grupo": "G",
        "cor": "Lilás",
        "selecoes": [
            {"sigla": "BEL", "nome": "Belgium"},
            {"sigla": "EGY", "nome": "Egypt"},
            {"sigla": "IRN", "nome": "IR Iran"},
            {"sigla": "NZL", "nome": "New Zealand"},
        ],
    },
    {
        "grupo": "H",
        "cor": "Turquesa",
        "selecoes": [
            {"sigla": "ESP", "nome": "Spain"},
            {"sigla": "CPV", "nome": "Cabo Verde"},
            {"sigla": "KSA", "nome": "Saudi Arabia"},
            {"sigla": "URU", "nome": "Uruguay"},
        ],
    },
    {
        "grupo": "I",
        "cor": "Azul Escuro",
        "selecoes": [
            {"sigla": "FRA", "nome": "France"},
            {"sigla": "SEN", "nome": "Senegal"},
            {"sigla": "IRQ", "nome": "Iraq"},
            {"sigla": "NOR", "nome": "Norway"},
        ],
    },
    {
        "grupo": "J",
        "cor": "Rosa Claro",
        "selecoes": [
            {"sigla": "ARG", "nome": "Argentina"},
            {"sigla": "ALG", "nome": "Algeria"},
            {"sigla": "AUT", "nome": "Austria"},
            {"sigla": "JOR", "nome": "Jordan"},
        ],
    },
    {
        "grupo": "K",
        "cor": "Magenta",
        "selecoes": [
            {"sigla": "POR", "nome": "Portugal"},
            {"sigla": "COD", "nome": "Congo DR"},
            {"sigla": "UZB", "nome": "Uzbekistan"},
            {"sigla": "COL", "nome": "Colombia"},
        ],
    },
    {
        "grupo": "L",
        "cor": "Marrom",
        "selecoes": [
            {"sigla": "ENG", "nome": "England"},
            {"sigla": "CRO", "nome": "Croatia"},
            {"sigla": "GHA", "nome": "Ghana"},
            {"sigla": "PAN", "nome": "Panama"},
        ],
    },
]

EXTRA_GROUPS = [
    {
        "grupo": "Album",
        "cor": "Dourado",
        "selecoes": [
            {"sigla": "00", "nome": "Capa", "total": 1, "codes": ["00"]},
            {"sigla": "FWC", "nome": "Especiais", "total": 19},
        ],
    },
    {
        "grupo": "Coca-Cola",
        "cor": "Vermelho",
        "selecoes": [
            {"sigla": "CC", "nome": "Coca-Cola", "total": 14},
        ],
    },
]

TEAM_STICKERS_PER_SELECTION = 20


def codes_for_selection(selection):
    if "codes" in selection:
        return selection["codes"]
    total = selection.get("total", TEAM_STICKERS_PER_SELECTION)
    return [f"{selection['sigla']}-{number}" for number in range(1, total + 1)]


def sticker_number(code, selection_sigla):
    if code == "00":
        return "00"
    prefix = f"{selection_sigla}-"
    if code.startswith(prefix):
        return code.removeprefix(prefix)
    return code


def iter_groups():
    return TEAM_GROUPS + EXTRA_GROUPS


def find_selection(selection_sigla):
    normalized_sigla = selection_sigla.upper()
    for group in iter_groups():
        for selection in group["selecoes"]:
            if selection["sigla"] == normalized_sigla:
                return group, selection
    return None, None


def all_album_codes():
    codes = []
    for group in iter_groups():
        for selection in group["selecoes"]:
            codes.extend(codes_for_selection(selection))
    return codes


def percent(completed, total):
    if not total:
        return 0
    return round((completed / total) * 100)


def build_dashboard_data(collected_codes):
    sections = []
    total_completed = 0
    total_stickers = 0

    for group in TEAM_GROUPS + EXTRA_GROUPS:
        teams = []
        group_completed = 0
        group_total = 0

        for selection in group["selecoes"]:
            codes = codes_for_selection(selection)
            completed = sum(1 for code in codes if code in collected_codes)
            total = len(codes)
            group_completed += completed
            group_total += total
            teams.append(
                {
                    "sigla": selection["sigla"],
                    "nome": selection["nome"],
                    "href": selection["sigla"].lower(),
                    "completed": completed,
                    "total": total,
                    "percent": percent(completed, total),
                }
            )

        total_completed += group_completed
        total_stickers += group_total
        sections.append(
            {
                "grupo": group["grupo"],
                "cor": group["cor"],
                "teams": teams,
                "completed": group_completed,
                "total": group_total,
                "percent": percent(group_completed, group_total),
            }
        )

    return {
        "sections": sections,
        "completed": total_completed,
        "total": total_stickers,
        "percent": percent(total_completed, total_stickers),
    }


def build_selection_data(selection_sigla, collected_codes, pending_only=False):
    group, selection = find_selection(selection_sigla)
    if not selection:
        return None

    stickers = []
    for code in codes_for_selection(selection):
        collected = code in collected_codes
        if pending_only and collected:
            continue
        stickers.append(
            {
                "code": code,
                "number": sticker_number(code, selection["sigla"]),
                "collected": collected,
            }
        )

    total_codes = codes_for_selection(selection)
    completed = sum(1 for code in total_codes if code in collected_codes)
    total = len(total_codes)

    return {
        "grupo": group["grupo"],
        "cor": group["cor"],
        "sigla": selection["sigla"],
        "nome": selection["nome"],
        "completed": completed,
        "total": total,
        "percent": percent(completed, total),
        "pending": total - completed,
        "pending_only": pending_only,
        "stickers": stickers,
    }
