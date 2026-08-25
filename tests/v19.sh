#!/bin/bash -euo pipefail

if [[ -r /etc/inithooks.conf ]]; then
    # shellcheck disable=SC1091
    . /etc/inithooks.conf
fi

host=${1:-${APP_DOMAIN:-localhost}}
password=${2:-${TKL_TEST_APP_PASS:-${APP_PASS:-}}}
[[ -n "$password" && -n "${TKL_TEST_RESULT:-}" ]] || {
    echo "TKL_TEST_APP_PASS and TKL_TEST_RESULT are required" >&2
    exit 2
}

base="https://$host"
resolve=(--resolve "$host:443:127.0.0.1")
tmp=$(mktemp -d /tmp/simplemachines-v19.XXXXXX)
cleanup() {
    if [[ -s "$tmp/fixture" ]]; then
        board_id=$(sed -n 's/^board_id=//p' "$tmp/fixture")
        topic_id=$(sed -n 's/^topic_id=//p' "$tmp/fixture")
        if [[ "$board_id" =~ ^[0-9]+$ && "$topic_id" =~ ^[0-9]+$ ]]; then
            php "$(dirname "$0")/content-fixture.php" cleanup "$board_id" "$topic_id" || true
        fi
    fi
    find "$tmp" -depth -delete
}
trap cleanup EXIT

for service in apache2 mariadb; do
    systemctl is-active --quiet "$service"
done

curl --fail --insecure --silent --show-error "${resolve[@]}" \
    "$base/" --output "$tmp/front"
grep -q 'Simple Machines' "$tmp/front"

cookie="$tmp/cookie"
curl --fail --insecure --silent --show-error \
    "${resolve[@]}" --cookie-jar "$cookie" \
    "$base/index.php?action=login" --output "$tmp/login"
form_data=$(python3 - "$tmp/login" <<'PY'
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode
import sys

class LoginForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_form = False
        self.values = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form" and attrs.get("id") == "frmLogin":
            self.in_form = True
        elif self.in_form and tag == "input" and attrs.get("type") == "hidden":
            if attrs.get("name"):
                self.values.append((attrs["name"], attrs.get("value", "")))

    def handle_endtag(self, tag):
        if tag == "form" and self.in_form:
            self.in_form = False

parser = LoginForm()
parser.feed(Path(sys.argv[1]).read_text(errors="replace"))
if len(parser.values) < 2:
    raise SystemExit("login form tokens were not found")
print(urlencode(parser.values))
PY
)

curl --fail --insecure --silent --show-error --location \
    "${resolve[@]}" --cookie "$cookie" --cookie-jar "$cookie" \
    --data "$form_data" --data-urlencode 'user=admin' \
    --data-urlencode "passwrd=$password" --data 'cookielength=-1' \
    "$base/index.php?action=login2" --output "$tmp/authenticated"
grep -q 'action=logout' "$tmp/authenticated"
grep -q 'action=admin' "$tmp/authenticated"

token="$(date +%s)-$$"
php "$(dirname "$0")/content-fixture.php" create "$token" > "$tmp/fixture"
board_id=$(sed -n 's/^board_id=//p' "$tmp/fixture")
topic_id=$(sed -n 's/^topic_id=//p' "$tmp/fixture")
board_name=$(sed -n 's/^board_name=//p' "$tmp/fixture")
topic_subject=$(sed -n 's/^topic_subject=//p' "$tmp/fixture")
topic_body=$(sed -n 's/^topic_body=//p' "$tmp/fixture")

curl --fail --insecure --silent --show-error \
    "${resolve[@]}" "$base/index.php?board=$board_id.0" --output "$tmp/board"
grep -Fq "$board_name" "$tmp/board"
grep -Fq "$topic_subject" "$tmp/board"
curl --fail --insecure --silent --show-error \
    "${resolve[@]}" "$base/index.php?topic=$topic_id.0" --output "$tmp/topic"
grep -Fq "$topic_subject" "$tmp/topic"
grep -Fq "$topic_body" "$tmp/topic"

db_row=$(mysql --batch --skip-column-names simplemachines --execute \
    "SELECT CONCAT(b.name, '|', m.subject, '|', m.body) FROM boards b JOIN topics t ON t.id_board=b.id_board JOIN messages m ON m.id_msg=t.id_first_msg WHERE b.id_board=$board_id AND t.id_topic=$topic_id;")
[[ "$db_row" == "$board_name|$topic_subject|$topic_body" ]]

update_output=$(simplemachines-update --check)
grep -q '^installed=2\.1\.7$' <<<"$update_output"
grep -q '^latest=2\.1\.' <<<"$update_output"
grep -Eq '^status=(current|update-available)$' <<<"$update_output"
updater_status=$(sed -n 's/^status=//p' <<<"$update_output")

php "$(dirname "$0")/content-fixture.php" cleanup "$board_id" "$topic_id"
: > "$tmp/fixture"
remaining=$(mysql --batch --skip-column-names simplemachines --execute \
    "SELECT COUNT(*) FROM boards WHERE id_board=$board_id;")
[[ "$remaining" == 0 ]]

{
    echo 'package_source=github.com/SimpleMachines/SMF tag v2.1.7'
    echo 'installed_version=2.1.7'
    echo 'runtime_checks=services,https,admin-login,board-topic-create-read,database,cleanup'
    echo 'updater_command=simplemachines-update --check'
    echo "updater_result=$updater_status"
    echo 'updater_channel=github.com/SimpleMachines/SMF stable releases'
    echo 'integrity_evidence=sha256:2c9c0ea7df803ee03ff7755ea3651c680952e264b7c572439902bb18245c06a3'
} > "$TKL_TEST_RESULT"

echo "Simple Machines v19 acceptance: PASS"
