from django.contrib.postgres.operations import (
    BtreeGistExtension,
    CITextExtension,
    TrigramExtension,
    UnaccentExtension,
)
from django.db import migrations


class Migration(migrations.Migration):
    """Extensions required by the schema (citext emails/codes, trigram search, tax-rule exclusion)."""

    initial = True
    dependencies = []
    operations = [CITextExtension(), TrigramExtension(), UnaccentExtension(), BtreeGistExtension()]
