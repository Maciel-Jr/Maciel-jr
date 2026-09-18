
import os
import requests
from collections import defaultdict

TOKEN = os.environ["GH_STATS_TOKEN"]
USERNAME = os.environ["GITHUB_ACTOR"]

API = "https://api.github.com"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
    "X-GitHub-Api-Version": "2026-03-10",
}

session = requests.Session()
session.headers.update(HEADERS)


def get_repositories():
    repositories = []

    page = 1

    while True:
        response = session.get(
            f"{API}/user/repos",
            params={
                "visibility": "all",
                "affiliation": "owner,organization_member",
                "per_page": 100,
                "page": page,
            },
        )

        response.raise_for_status()

        data = response.json()

        if not data:
            break

        repositories.extend(data)

        if len(data) < 100:
            break

        page += 1

    return repositories


def get_languages(owner, repo):
    response = session.get(
        f"{API}/repos/{owner}/{repo}/languages"
    )

    response.raise_for_status()

    return response.json()


def generate_svg(languages):
    width = 900
    height = 420

    total = sum(languages.values())

    if total == 0:
        return """
<svg xmlns="http://www.w3.org/2000/svg"
     width="900"
     height="420"
     viewBox="0 0 900 420">

    <rect width="900" height="420"
          fill="#0d1117"/>

    <text x="40" y="60"
          fill="#58a6ff"
          font-size="28"
          font-family="Arial">
        Most Used Languages
    </text>

    <text x="40" y="120"
          fill="#8b949e"
          font-size="18"
          font-family="Arial">
        No language data found
    </text>

</svg>
"""

    colors = [
        "#F1E05A",
        "#3178C6",
        "#3572A5",
        "#00ADD8",
        "#DA5B0B",
        "#563D7C",
        "#178600",
        "#E34C26",
        "#F34B7D",
        "#844FBA",
    ]

    items = sorted(
        languages.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:8]

    # Soma das linguagens exibidas
    displayed_total = sum(value for _, value in items)

    x = 40
    bar_y = 100
    bar_width = 820
    bar_height = 18

    svg = f"""
<svg xmlns="http://www.w3.org/2000/svg"
     width="{width}"
     height="{height}"
     viewBox="0 0 {width} {height}">

    <rect width="{width}"
          height="{height}"
          rx="12"
          fill="#0d1117"/>

    <text x="40"
          y="55"
          fill="#58a6ff"
          font-size="28"
          font-family="Arial">
        Most Used Languages
    </text>
"""

    current_x = x

    for index, (language, value) in enumerate(items):
        percentage = value / displayed_total * 100

        segment_width = bar_width * percentage / 100

        color = colors[index % len(colors)]

        svg += f"""
    <rect
        x="{current_x}"
        y="{bar_y}"
        width="{segment_width}"
        height="{bar_height}"
        fill="{color}"/>
"""

        current_x += segment_width

    # Legenda
    legend_y = 170

    for index, (language, value) in enumerate(items):
        percentage = value / displayed_total * 100

        column = index % 2
        row = index // 2

        lx = 50 + column * 400
        ly = legend_y + row * 55

        color = colors[index % len(colors)]

        svg += f"""
    <circle
        cx="{lx}"
        cy="{ly - 6}"
        r="7"
        fill="{color}"/>

    <text
        x="{lx + 20}"
        y="{ly}"
        fill="#8b949e"
        font-size="17"
        font-family="Arial">
        {language} {percentage:.2f}%
    </text>
"""

    svg += """
</svg>
"""

    return svg


def main():
    repositories = get_repositories()

    print(f"Repositórios encontrados: {len(repositories)}")

    languages = defaultdict(int)

    selected_repositories = []

    for repo in repositories:

        owner = repo["owner"]["login"]
        owner_type = repo["owner"]["type"]

        private = repo["private"]

        # Seus próprios repositórios
        own_repo = (
            owner.lower() == USERNAME.lower()
        )

        # Repositórios de organizações
        organization_repo = (
            owner_type == "Organization"
        )

        # Queremos privados próprios
        # + privados pertencentes a organizações
        if not private:
            continue

        if not (own_repo or organization_repo):
            continue

        selected_repositories.append(
            repo["full_name"]
        )

        print(
            f"Analisando: {repo['full_name']}"
        )

        repo_languages = get_languages(
            owner,
            repo["name"]
        )

        for language, bytes_count in repo_languages.items():
            languages[language] += bytes_count

    print()
    print("Repositórios analisados:")
    
    for repo in selected_repositories:
        print(f" - {repo}")

    print()
    print("Linguagens:")

    for language, value in sorted(
        languages.items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        print(f" - {language}: {value}")

    svg = generate_svg(languages)

    os.makedirs("profile", exist_ok=True)

    with open(
        "profile/top-langs-all.svg",
        "w",
        encoding="utf-8",
    ) as file:
        file.write(svg)

    print()
    print("SVG gerado:")
    print("profile/top-langs-all.svg")


if __name__ == "__main__":
    main()
