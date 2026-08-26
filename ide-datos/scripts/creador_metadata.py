"""Generate ISO 19139 XML metadata for every dataset in the catalogue.

The IDERA vector metadata profile v2.0 is ISO 19115 encoded as ISO 19139 XML,
and defines 26 elements of which 17 are mandatory. This script builds that XML
from what the pipeline already knows: the derived catalogue plus the QGIS .qmd
sidecar. Nothing is invented - an element with no source is left out and
reported as a compliance gap.

This replaces the script of the same name in the old repository, which wrote
`topiccategory: boundaries` hardcoded for every layer, `geomtype: unknown`, a
fixed bounding box of the whole ejido, and defined CRS_EPSG without ever
writing it.

Usage:
    py -3 ide-datos/scripts/creador_metadata.py
    py -3 ide-datos/scripts/creador_metadata.py --estricto
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comun  # noqa: E402

NS = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
    "gml": "http://www.opengis.net/gml/3.2",
    "xlink": "http://www.w3.org/1999/xlink",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}
for prefijo, uri in NS.items():
    ET.register_namespace(prefijo, uri)

LISTA_CODIGOS = (
    "http://standards.iso.org/ittf/PubliclyAvailableStandards/"
    "ISO_19139_Schemas/resources/Codelist/gmxCodelists.xml"
)

# The 17 mandatory elements of the IDERA vector profile v2.0, by its own ids.
OBLIGATORIOS = {
    "A1": "Título",
    "A2": "Fecha de referencia",
    "A2.1": "Tipo de fecha de referencia",
    "A4": "Resumen",
    "A6": "Punto de contacto del creador",
    "A7": "Punto de contacto del metadato",
    "A8": "Frecuencia de mantenimiento",
    "A9": "Tema (topicCategory)",
    "A10": "Palabras clave",
    "A11": "Restricciones",
    "A12": "Tipo de representación espacial",
    "A14": "Idioma de los datos",
    "A15": "Conjunto de caracteres",
    "B1": "Proyección",
    "C1": "Enlace de descarga",
    "E1": "Identificador del metadato",
    "E6": "Fecha de creación del metadato",
}


def q(prefijo, etiqueta):
    return f"{{{NS[prefijo]}}}{etiqueta}"


def sub(padre, nombre, **atributos):
    prefijo, etiqueta = nombre.split(":")
    return ET.SubElement(padre, q(prefijo, etiqueta), atributos)


def texto(padre, nombre, valor, tipo="gco:CharacterString"):
    """<gmd:x><gco:CharacterString>valor</gco:CharacterString></gmd:x>"""
    nodo = sub(padre, nombre)
    hijo = sub(nodo, tipo)
    hijo.text = valor
    return nodo


def codigo(padre, nombre, clase, valor):
    """A codelist element: <gmd:x><gmd:ClassCode codeListValue="v"/></gmd:x>"""
    nodo = sub(padre, nombre)
    hijo = sub(
        nodo,
        f"gmd:{clase}",
        codeList=f"{LISTA_CODIGOS}#{clase}",
        codeListValue=valor,
    )
    hijo.text = valor
    return nodo


def parte_responsable(padre, nombre, organizacion, email, rol):
    nodo = sub(padre, nombre)
    parte = sub(nodo, "gmd:CI_ResponsibleParty")
    if organizacion:
        texto(parte, "gmd:organisationName", organizacion)
    if email:
        contacto = sub(parte, "gmd:contactInfo")
        ci = sub(contacto, "gmd:CI_Contact")
        direccion = sub(ci, "gmd:address")
        ci_address = sub(direccion, "gmd:CI_Address")
        texto(ci_address, "gmd:electronicMailAddress", email)
    codigo(parte, "gmd:role", "CI_RoleCode", rol)
    return nodo


def construir(fila, meta, fecha_metadato):
    """Build one MD_Metadata tree. Returns (element, missing_ids)."""
    faltan = []

    def exige(clave, valor):
        if not valor:
            faltan.append(clave)
        return valor

    raiz = ET.Element(q("gmd", "MD_Metadata"))

    # E1 -- file identifier
    texto(raiz, "gmd:fileIdentifier", exige("E1", fila.get("id", "")))

    # A14/A15 at metadata level. The .qmd carries ARG in <language>, which is a
    # country code, not a language, so the profile value is set here instead.
    codigo(raiz, "gmd:language", "LanguageCode", "spa")
    codigo(raiz, "gmd:characterSet", "MD_CharacterSetCode", "utf8")
    codigo(raiz, "gmd:hierarchyLevel", "MD_ScopeCode", "dataset")

    # A7 -- metadata point of contact
    organizacion = meta.get("organizacion") or fila.get("organizacion", "")
    email = meta.get("contacto_email") or fila.get("contacto_email", "")
    exige("A7", email or organizacion)
    parte_responsable(
        raiz, "gmd:contact", organizacion, email, "pointOfContact"
    )

    # E6 -- metadata creation date
    nodo = sub(raiz, "gmd:dateStamp")
    sub(nodo, "gco:Date").text = exige("E6", fecha_metadato)

    texto(raiz, "gmd:metadataStandardName", "ISO 19115:2003/19139")
    texto(raiz, "gmd:metadataStandardVersion", "1.0")

    # B1 -- reference system
    crs = exige("B1", fila.get("crs", ""))
    if crs:
        nodo = sub(raiz, "gmd:referenceSystemInfo")
        sistema = sub(nodo, "gmd:MD_ReferenceSystem")
        identificador = sub(sistema, "gmd:referenceSystemIdentifier")
        rs = sub(identificador, "gmd:RS_Identifier")
        texto(rs, "gmd:code", crs)

    # --- identification ---
    ident = sub(sub(raiz, "gmd:identificationInfo"), "gmd:MD_DataIdentification")

    cita = sub(sub(ident, "gmd:citation"), "gmd:CI_Citation")
    texto(cita, "gmd:title", exige("A1", fila.get("titulo", "")))

    # A2 / A2.1 -- reference date. fecha_modificacion comes from Git, so it is
    # the real date the data last changed, not a date somebody typed.
    fecha = exige("A2", (fila.get("fecha_modificacion", "") or "")[:10])
    if fecha:
        nodo = sub(sub(cita, "gmd:date"), "gmd:CI_Date")
        interno = sub(nodo, "gmd:date")
        sub(interno, "gco:Date").text = fecha
        codigo(nodo, "gmd:dateType", "CI_DateTypeCode", "revision")
        faltan_tipo = False
    else:
        faltan_tipo = True
    if faltan_tipo:
        faltan.append("A2.1")

    # A4 -- abstract
    resumen = fila.get("resumen_metadato") or fila.get("descripcion", "")
    texto(ident, "gmd:abstract", exige("A4", resumen))

    # A6 -- creator point of contact
    exige("A6", email or organizacion)
    parte_responsable(ident, "gmd:pointOfContact", organizacion, email, "owner")

    # A8 -- maintenance frequency
    frecuencia = exige("A8", fila.get("frecuencia_actualizacion", ""))
    if frecuencia:
        nodo = sub(ident, "gmd:resourceMaintenance")
        mantenimiento = sub(nodo, "gmd:MD_MaintenanceInformation")
        codigo(
            mantenimiento,
            "gmd:maintenanceAndUpdateFrequency",
            "MD_MaintenanceFrequencyCode",
            frecuencia,
        )

    # A10 -- descriptive keywords
    palabras = [p for p in (fila.get("palabras_clave", "") or "").split("|") if p]
    exige("A10", palabras)
    if palabras:
        nodo = sub(ident, "gmd:descriptiveKeywords")
        bloque = sub(nodo, "gmd:MD_Keywords")
        for palabra in palabras:
            texto(bloque, "gmd:keyword", palabra)

    # A11 -- constraints
    licencia = exige("A11", fila.get("licencia", ""))
    if licencia:
        nodo = sub(ident, "gmd:resourceConstraints")
        restricciones = sub(nodo, "gmd:MD_LegalConstraints")
        texto(restricciones, "gmd:useLimitation", licencia)
        codigo(
            restricciones, "gmd:accessConstraints", "MD_RestrictionCode", "otherRestrictions"
        )
        texto(restricciones, "gmd:otherConstraints", licencia)

    # A12 -- spatial representation type
    codigo(
        ident, "gmd:spatialRepresentationType", "MD_SpatialRepresentationTypeCode", "vector"
    )
    exige("A12", "vector")

    codigo(ident, "gmd:language", "LanguageCode", "spa")
    exige("A14", "spa")
    codigo(ident, "gmd:characterSet", "MD_CharacterSetCode", "utf8")
    exige("A15", "utf8")

    # A9 -- topic category
    tema = exige("A9", fila.get("categoria_iso", ""))
    if tema:
        nodo = sub(ident, "gmd:topicCategory")
        sub(nodo, "gmd:MD_TopicCategoryCode").text = tema

    # Geographic extent, from the bbox the pipeline derives in WGS 84.
    bbox = (fila.get("bbox_4326", "") or "").split(",")
    if len(bbox) == 4:
        nodo = sub(sub(ident, "gmd:extent"), "gmd:EX_Extent")
        geografico = sub(nodo, "gmd:geographicElement")
        caja = sub(geografico, "gmd:EX_GeographicBoundingBox")
        for etiqueta, valor in (
            ("westBoundLongitude", bbox[0]),
            ("eastBoundLongitude", bbox[2]),
            ("southBoundLatitude", bbox[1]),
            ("northBoundLatitude", bbox[3]),
        ):
            texto(caja, f"gmd:{etiqueta}", valor, tipo="gco:Decimal")

    # C1 -- online linkage
    enlace = exige("C1", fila.get("url_descarga", ""))
    if enlace:
        distribucion = sub(sub(raiz, "gmd:distributionInfo"), "gmd:MD_Distribution")
        opciones = sub(
            sub(distribucion, "gmd:transferOptions"), "gmd:MD_DigitalTransferOptions"
        )
        for url, nombre in (
            (enlace, f"{fila['id']}.gpkg"),
            (fila.get("url_descarga_geojson", ""), f"{fila['id']}.geojson"),
        ):
            if not url:
                continue
            recurso = sub(sub(opciones, "gmd:onLine"), "gmd:CI_OnlineResource")
            nodo = sub(recurso, "gmd:linkage")
            sub(nodo, "gmd:URL").text = url
            texto(recurso, "gmd:name", nombre)
            codigo(recurso, "gmd:function", "CI_OnLineFunctionCode", "download")

    # Lineage, optional in the profile but the reason the data is trustworthy.
    linaje = meta.get("linaje") or fila.get("linaje", "")
    if linaje:
        calidad = sub(sub(raiz, "gmd:dataQualityInfo"), "gmd:DQ_DataQuality")
        alcance = sub(calidad, "gmd:scope")
        codigo(sub(alcance, "gmd:DQ_Scope"), "gmd:level", "MD_ScopeCode", "dataset")
        texto(sub(sub(calidad, "gmd:lineage"), "gmd:LI_Lineage"), "gmd:statement", linaje)

    return raiz, faltan


def escribir(raiz, destino):
    crudo = ET.tostring(raiz, encoding="utf-8")
    bonito = minidom.parseString(crudo).toprettyxml(indent="  ", encoding="utf-8")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(bonito)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--estricto",
        action="store_true",
        help="salir con error si falta algún elemento obligatorio de IDERA",
    )
    parser.add_argument("--salida", help="directorio de salida")
    parser.add_argument("--fecha", help="fecha del metadato en ISO (por defecto, hoy)")
    args = parser.parse_args()

    raiz_datos = comun.raiz_datos()
    catalogo = raiz_datos / "catalogo" / "catalogo_completo.json"
    if not catalogo.exists():
        print("[ERROR] falta catalogo_completo.json - correr derivar_catalogo.py")
        return 1

    if args.fecha:
        fecha_metadato = args.fecha
    else:
        import datetime

        fecha_metadato = datetime.date.today().isoformat()

    salida = Path(args.salida) if args.salida else raiz_datos / "derivados" / "iso19139"
    salida.mkdir(parents=True, exist_ok=True)

    with open(catalogo, encoding="utf-8") as fh:
        filas = json.load(fh)

    incompletos = 0
    for fila in filas:
        did = fila["id"]
        tema = comun.tema_de(did)
        qmd = comun.ruta_maestro(did, tema, "qmd")
        meta = comun.leer_qmd(qmd) if qmd.exists() else {}

        arbol, faltan = construir(fila, meta, fecha_metadato)
        destino = salida / f"{did}.xml"
        escribir(arbol, destino)

        if faltan:
            incompletos += 1
            detalle = ", ".join(f"{c} ({OBLIGATORIOS[c]})" for c in faltan)
            print(f"  {destino.name}: faltan {len(faltan)} obligatorio(s) - {detalle}")
        else:
            print(f"  {destino.name}: completo, 17/17 obligatorios de IDERA")

    print()
    print(f"{len(filas)} metadato(s) en {salida}")
    if incompletos:
        print(
            f"{incompletos} no cumple(n) todavía el perfil IDERA v2.0. El XML se "
            "genera igual, pero no está listo para cosecha."
        )
    return 1 if (incompletos and args.estricto) else 0


if __name__ == "__main__":
    sys.exit(main())
