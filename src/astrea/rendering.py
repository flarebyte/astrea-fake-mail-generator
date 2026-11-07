"""Fixture construction, explicit MIME serialization, and semantic expectations."""

import base64
import copy
import hashlib
import html
import json
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from email import policy
from email.message import EmailMessage
from email.utils import format_datetime, formataddr
from importlib.resources import files

from faker import Faker

from .assets import ASSETS
from .catalog import FIXTURES, REGIONS
from .errors import AstreaError
from .planning import digest, domain

POLICY = policy.SMTP.clone(max_line_length=78, utf8=False, cte_type="7bit")
TEMPLATES = json.loads(files("astrea").joinpath("data/templates.json").read_text())


def sha(data):
    return hashlib.sha256(data).hexdigest()


@dataclass
class Rendered:
    data: bytes
    entry: dict
    assets: set


def text_part(text, subtype="plain", cte="quoted-printable"):
    msg = EmailMessage(policy=POLICY)
    msg.set_content(text, subtype=subtype, charset="utf-8", cte=cte)
    if text == "":
        msg.set_payload("")
    return msg


def container(subtype, children):
    msg = EmailMessage(policy=POLICY)
    msg.set_type("multipart/" + subtype)
    for child in children:
        msg.attach(child)
    return msg


def attachment(data, media_type, filename, disposition="attachment", cid=None):
    part = EmailMessage(policy=POLICY)
    major, minor = media_type.split("/", 1)
    part.set_content(data, maintype=major, subtype=minor, cte="base64")
    part.add_header("Content-Disposition", disposition, filename=filename)
    if cid:
        part["Content-ID"] = cid
    return part


def walk(root):
    stack = [(root, "1", 1)]
    while stack:
        part, path, depth = stack.pop()
        yield part, path, depth
        payload = part.get_payload()
        if isinstance(payload, list):
            stack.extend(
                (child, f"{path}.{i}", depth + 1)
                for i, child in reversed(list(enumerate(payload, 1)))
            )


def message_id(plan, message):
    return f"<astrea-{digest(plan, message, 'message-id')}@{domain(plan, message, 2)}>"


def content(plan, message):
    key, locale = message["fixture_id"], message["locale"]
    template = TEMPLATES[locale]
    fake = Faker(locale)
    fake.seed_instance(int(digest(plan, message, "recipient-name"), 16))
    name = unicodedata.normalize("NFC", fake.name())
    body = unicodedata.normalize("NFC", template["body"].format(name=name))
    facts = template["facts"].copy()
    subject = template["subject"]
    if key == "fixture.us.pdf":
        subject, body, facts = (
            "Invoice for your order",
            f"Hello {name},\nYour invoice total is USD 24.00.",
            ["USD 24.00"],
        )
    if key == "fixture.uk.empty":
        body, facts = "", []
    if key == "fixture.uk.thread":
        member = message["thread_member_index"]
        subject = ("Re: " if member else "") + "Support request"
        body = [
            "Please help with the test order.",
            "We are checking the test order.\n> Please help with the test order.",
            "The test order is resolved.\n> We are checking the test order.",
        ][member]
        facts = ["test order"]
    cte = "7bit" if body.isascii() else "quoted-printable"
    if key == "fixture.uk.alternative":
        cte = "quoted-printable"
    plain = text_part(body, cte=cte)
    direction = ' dir="rtl"' if locale == "ar_EG" else ""
    markup = f'<html lang="{locale.replace("_", "-")}"{direction}><body><p>{html.escape(body).replace(chr(10), "<br>")}</p></body></html>'
    html_part = text_part(
        markup, "html", "base64" if key == "fixture.es.encoded" else "quoted-printable"
    )
    used = set()
    if key == "fixture.us.html":
        root = html_part
    elif key == "fixture.fr.inline":
        cid = f"<logo@{domain(plan, message, 3)}>"
        markup = markup.replace(
            "</body>", f'<img src="cid:{cid[1:-1]}" alt="Logo"></body>'
        )
        html_part = text_part(markup, "html")
        image = attachment(
            ASSETS["logo.png"][1], "image/png", "logo.png", "inline", cid
        )
        root = container(
            "alternative", [plain, container("related", [html_part, image])]
        )
        used.add("logo.png")
    elif key in {
        "fixture.uk.alternative",
        "fixture.es.encoded",
        "fixture.it.list",
        "fixture.jp.notification",
    }:
        root = container("alternative", [plain, html_part])
    elif key in {
        "fixture.us.pdf",
        "fixture.de.attachments",
        "fixture.ar.notification",
        "fixture.stress.filename",
    }:
        parts = [plain]
        names = ["invoice.pdf"]
        if key == "fixture.de.attachments":
            parts = [container("alternative", [plain, html_part])]
            names = ["logo.png", "photo.jpg", "invoice.pdf", "notes.txt", "report.csv"]
        if key == "fixture.ar.notification":
            parts = [container("alternative", [plain, html_part])]
            names = ["notes.txt"]
        if key == "fixture.stress.filename":
            names = ["notes.txt"]
        for name_asset in names:
            media, data = ASSETS[name_asset]
            filename = name_asset
            if key == "fixture.de.attachments" and name_asset == "notes.txt":
                filename = "März-Notizen.txt"
            if key == "fixture.ar.notification":
                filename = "ملاحظات.txt"
            if key == "fixture.stress.filename":
                filename = {
                    "traversal": "../../outside.txt",
                    "absolute": "/tmp/outside.txt",
                    "bidi": "notes\u202etxt.txt",
                }[message["parameters"]["filename_case"]]
            parts.append(attachment(data, media, filename))
            used.add(name_asset)
        root = container("mixed", parts)
    elif key == "fixture.us.forward":
        inner = text_part("This is the original synthetic message.", cte="7bit")
        inner["From"] = f"original@{domain(plan, message, 0)}"
        inner["To"] = f"reader@{domain(plan, message, 1)}"
        inner["Subject"] = "Original synthetic message"
        inner["Date"] = format_datetime(datetime.fromisoformat(message["date"]))
        inner["Message-ID"] = (
            f"<attached-{digest(plan, message, 'attached-id')}@{domain(plan, message, 2)}>"
        )
        embedded = EmailMessage(policy=POLICY)
        embedded.set_type("message/rfc822")
        embedded.set_payload([inner])
        embedded.add_header(
            "Content-Disposition", "attachment", filename="forwarded.eml"
        )
        root = container("mixed", [plain, embedded])
    elif key in {"fixture.uk.nested", "fixture.stress.depth"}:
        root = container("alternative", [plain, html_part])
        for _ in range(message["parameters"]["depth"] - 2):
            root = container("mixed", [root])
    elif key == "fixture.stress.width":
        children = []
        for _ in range(message["parameters"]["total_parts"] - 1):
            child = EmailMessage(policy=POLICY)
            child["Content-Type"] = "text/plain"
            child.set_payload("")
            children.append(child)
        root = container("mixed", children)
        facts = []
    elif key in {"fixture.stress.boundary", "fixture.stress.truncated"}:
        root = container("mixed", [container("alternative", [plain, html_part])])
    else:
        root = plain
    return root, subject, facts, name, used


def with_headers(plan, message, root, subject, name):
    # Header order is deliberately built before MIME headers.
    msg = EmailMessage(policy=POLICY)
    index = message["period_index"]
    participant = dict(message)
    if message["fixture_id"] == "fixture.uk.thread":
        participant["period_index"] = index - message["thread_member_index"]
    sender = f"morgan@{domain(plan, participant, 0)}"
    recipient = f"alex@{domain(plan, participant, 1)}"
    instant = format_datetime(datetime.fromisoformat(message["date"]))
    msg["Return-Path"] = f"<{sender}>"
    for hop in range(2):
        msg["Received"] = (
            f"from {domain(plan, message, 4 + hop)} ([192.0.2.{10 + hop}]) by {domain(plan, message, 5 + hop)}; {instant}"
        )
    provider = message["profiles"]["provider"]["id"]
    if provider != "provider.generic":
        msg["Authentication-Results"] = (
            f"{domain(plan, message, 4)}; none (synthetic fixture); smtp.mailfrom={domain(plan, message, 0)}"
        )
        if provider == "provider.gmail":
            msg["X-Received"] = f"by {domain(plan, message, 4)}; {instant}"
            msg["X-Google-Smtp-Source"] = (
                "Astrea-synthetic-" + digest(plan, message, "provider")[:24]
            )
        else:
            msg["X-MS-Exchange-Organization-AuthAs"] = "Anonymous"
            msg["X-MS-Exchange-Organization-SCL"] = "1"
    display_sender = {"ja_JP": "佐藤 花子", "ar_EG": "نور أحمد"}.get(
        message["locale"], "Morgan Ellis"
    )
    msg["From"] = formataddr((display_sender, sender))
    msg["To"] = formataddr((name, recipient))
    if message["fixture_id"] == "fixture.us.recipients":
        msg.replace_header(
            "To",
            ", ".join(
                formataddr(
                    (
                        f"Synthetic recipient {i}",
                        f"person{i}@{domain(plan, message, 1 + i)}",
                    )
                )
                for i in range(3)
            ),
        )
        msg["Cc"] = f"team@{domain(plan, message, 4)}"
        msg["Reply-To"] = sender
    msg["Date"] = instant
    msg["Message-ID"] = message_id(plan, message)
    msg["Subject"] = subject
    if message["fixture_id"] == "fixture.uk.thread" and message["thread_member_index"]:
        previous = []
        for member in range(message["thread_member_index"]):
            reference = dict(
                message,
                thread_member_index=member,
                period_index=index - message["thread_member_index"] + member,
            )
            previous.append(message_id(plan, reference))
        msg["In-Reply-To"] = previous[-1]
        msg["References"] = " ".join(previous)
    client = message["profiles"]["client"]["id"]
    if client == "client.thunderbird":
        msg["User-Agent"] = "Astrea Thunderbird-style test fixture"
        msg["Content-Language"] = message["locale"].replace("_", "-")
    elif client == "client.outlook-desktop":
        msg["X-Mailer"] = "Astrea Outlook-style test fixture"
        msg["Thread-Index"] = base64.b64encode(
            bytes.fromhex(digest(plan, message, "thread-index"))[:22]
        ).decode()
        msg["Thread-Topic"] = subject
    if message["fixture_id"] == "fixture.it.list":
        msg["List-ID"] = f"community.{domain(plan, message, 1)}"
        msg["List-Unsubscribe"] = f"<https://{domain(plan, message, 1)}/unsubscribe>"
    for key, value in root.raw_items():
        msg[key] = value
    msg.set_payload(root.get_payload())
    return msg


def expectations(root, facts, message, plan):
    nodes, attachments = [], []
    unicode_values = []
    for part, path, depth in walk(root):
        decoded = part.get_payload(decode=True)
        if (
            decoded is not None
            and part.get_content_maintype() == "text"
            and part["Content-Transfer-Encoding"] != "base64"
        ):
            decoded = decoded.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        if decoded is not None and part.get_content_maintype() == "text":
            unicode_values.append(decoded.decode(part.get_content_charset() or "ascii"))
        if part.get_filename():
            unicode_values.append(part.get_filename())
        nodes.append(
            {
                "path": path,
                "depth": depth,
                "media_type": part.get_content_type(),
                "charset": part.get_content_charset(),
                "disposition": part.get_content_disposition(),
                "content_id": str(part["Content-ID"]) if part["Content-ID"] else None,
                "transfer_encoding": str(part["Content-Transfer-Encoding"])
                if part["Content-Transfer-Encoding"]
                else None,
                "decoded_sha256": sha(decoded) if decoded is not None else None,
            }
        )
        if part.get_content_disposition() == "attachment":
            if part.get_content_type() == "message/rfc822":
                decoded = part.get_payload()[0].as_bytes(policy=POLICY)
            attachments.append(
                {
                    "path": path,
                    "filename": part.get_filename(),
                    "media_type": part.get_content_type(),
                    "size_bytes": len(decoded),
                    "sha256": sha(decoded),
                }
            )
    unicode_values.extend(str(value) for _, value in root.items())
    names = list(root.keys())
    decoded_values = {}
    for name in dict.fromkeys(names):
        values = [str(v) for v in root.get_all(name)]
        decoded_values[name] = values[0] if len(values) == 1 else values
    absent = ["Bcc"]
    if message["profiles"]["client"]["id"] != "client.outlook-desktop":
        absent.append("X-Mailer")
    thread = None
    if message["fixture_id"] == "fixture.uk.thread":
        thread = {
            "message_id": str(root["Message-ID"]),
            "in_reply_to": str(root["In-Reply-To"]) if root["In-Reply-To"] else None,
            "references": str(root["References"]).split() if root["References"] else [],
            "member_index": message["thread_member_index"],
        }
    return {
        "headers": {
            "ordered_names": names,
            "absent": absent,
            "decoded_values": decoded_values,
            "counts": {name: len(root.get_all(name)) for name in dict.fromkeys(names)},
        },
        "body_facts": facts,
        "bcc_recipients": (
            [f"hidden@{domain(plan, message, 5)}"]
            if message["fixture_id"] == "fixture.us.recipients"
            else []
        ),
        "unicode_codepoints": sorted(
            {
                f"U+{ord(char):04X}"
                for value in unicode_values
                for char in value
                if ord(char) > 127
            }
        ),
        "mime": {
            "depth": max(n["depth"] for n in nodes),
            "node_count": len(nodes),
            "nodes": nodes,
        },
        "attachments": attachments,
        "thread": thread,
        "stress": None,
    }


def enforce(root, data, expected, limits, malformed=False):
    mime = expected["mime"]
    for value, ceiling, field in [
        (len(data), limits["max_message_bytes"], "max_message_bytes"),
        (mime["depth"], limits["max_depth"], "max_depth"),
        (mime["node_count"], limits["max_parts"], "max_parts"),
        (len(expected["attachments"]), 20, "attachments"),
    ]:
        if value > ceiling:
            raise AstreaError(
                "E_LIMIT", "Generated message exceeds limit", field, ceiling
            )
    header_bytes = 0
    for part, _, _ in walk(root):
        header = part.as_bytes(policy=POLICY).split(b"\r\n\r\n", 1)[0]
        header_bytes += len(header) + 2
        for block in (
            header.replace(b"\r\n ", b" ").replace(b"\r\n\t", b" ").split(b"\r\n")
        ):
            if len(block) > 16384:
                raise AstreaError(
                    "E_LIMIT", "Single header exceeds limit", "headers", 16384
                )
    if header_bytes > limits["max_header_bytes"]:
        raise AstreaError(
            "E_LIMIT",
            "Header bytes exceed limit",
            "max_header_bytes",
            limits["max_header_bytes"],
        )
    if any(a["size_bytes"] > 2097152 for a in expected["attachments"]):
        raise AstreaError(
            "E_LIMIT", "Attachment exceeds decoded byte limit", "attachments", 2097152
        )
    if not malformed and any(len(line) > 998 for line in data.split(b"\r\n")):
        raise AstreaError(
            "E_LIMIT", "Serialized line exceeds 998 bytes", "headers", 998
        )


def render(plan, message):
    from .mutations import mutate

    root, subject, facts, name, used = content(plan, message)
    root = with_headers(plan, message, root, subject, name)
    # Deterministic explicit boundaries, checked against all encoded leaf payloads.
    for part, path, _ in walk(root):
        if part.get_content_maintype() == "multipart":
            boundary = "astrea-" + digest(plan, message, "boundary/" + path)[:40]
            if any(
                boundary in str(leaf.get_payload())
                for leaf, _, _ in walk(part)
                if not isinstance(leaf.get_payload(), list)
            ):
                raise AstreaError(
                    "E_ASSERTION", "Boundary collides with payload", exit_code=1
                )
            part.set_boundary(boundary)
    expected = expectations(root, facts, message, plan)
    data = root.as_bytes(policy=POLICY)
    row = FIXTURES[message["fixture_id"]]
    enforce(root, data, expected, plan["limits"])
    if row["pack"] == "stress":
        original = data
        data, stress = mutate(root, data, expected, message)
        expected["stress"] = stress
        if row["validity"] == "malformed" and message["fixture_id"] in {
            "fixture.stress.encoding",
            "fixture.stress.truncated",
        }:
            for node in expected["mime"]["nodes"]:
                node["decoded_sha256"] = None
        enforce(root, data, expected, plan["limits"], row["validity"] == "malformed")
        # Measure edits against the original header spans without parsing
        # malformed bytes. Payload and boundary-delimiter edits are not headers.
        headers = 0
        cursor = 0
        for part, _, _ in walk(root):
            header = part.as_bytes(policy=POLICY).split(b"\r\n\r\n", 1)[0] + b"\r\n"
            start = original.index(header, cursor)
            end = start + len(header)
            cursor = end
            headers += len(header)
            for edit in stress["edits"]:
                offset = edit["offset"]
                if start <= offset < end:
                    headers += len(base64.b64decode(edit["inserted_base64"]))
                headers -= max(
                    0, min(end, offset + edit["removed_bytes"]) - max(start, offset)
                )
        if headers > plan["limits"]["max_header_bytes"]:
            raise AstreaError(
                "E_LIMIT",
                "Mutated headers exceed limit",
                "max_header_bytes",
                plan["limits"]["max_header_bytes"],
            )
    region = REGIONS[message["locale"]]
    fake = Faker(message["locale"])
    effective = fake.get_formatter("name").__self__.__module__.rsplit(".", 1)[-1]
    entry = copy.deepcopy(message)
    entry.update(
        {
            "path": f"{message['index']:06d}-{message['fixture_id']}.eml",
            "seed_key": f"{message['period_id']}/{message['fixture_id']}/{message['locale']}/{message['occurrence']}/{message['thread_member_index']}",
            "region": region["id"],
            "script": region["scripts"],
            "effective_faker_locales": {"recipient_name": effective},
            "validity": row["validity"],
            "size_bytes": len(data),
            "sha256": sha(data),
            "expectations": expected,
            "concept": row["concept"],
            "tags": row["tags"].split(","),
        }
    )
    return Rendered(data, entry, used)
