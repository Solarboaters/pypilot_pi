"""Give the manually imported test archive its own download URL, not a CI template."""
import io
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET

package, = Path('package').glob('*aarch64_flatpak-25.08.tar.gz')
url = ('https://github.com/Solarboaters/pypilot_pi/releases/download/'
       'flatpak-arm64-25.08-test-20261124/' + package.name)
temporary = package.with_suffix('.final.gz')
with tarfile.open(package) as src, tarfile.open(temporary, 'w:gz') as dst:
    for member in src:
        if member.name == 'metadata.xml':
            root = ET.fromstring(src.extractfile(member).read())
            assert root.findtext('target').strip() == 'flatpak-aarch64'
            assert root.findtext('target-version').strip() == '25.08'
            root.find('tarball-url').text = url
            data = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            member.size = len(data)
            dst.addfile(member, io.BytesIO(data))
            Path('evidence/tested-metadata.xml').write_bytes(data)
        else:
            dst.addfile(member, src.extractfile(member) if member.isfile() else None)
temporary.replace(package)
Path('evidence', package.name).write_bytes(package.read_bytes())
