# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
import tempfile
from qgis.core import *
import uuid
from geoserverexplorer.geoserver.pki import PKICatalog

TEMP_CERT_FILE_PREFIX = "tmppki_"

_certFolder = None

def certFolder():
    global _certFolder
    if _certFolder is None:
        _certFolder = tempfile.mkdtemp()
    return _certFolder

def nonBasicAuthTypes():
    if QGis.QGIS_VERSION_INT < 20802:
        return [QgsAuthType.PkiPaths, QgsAuthType.PkiPkcs12]
    elif QGis.QGIS_VERSION_INT < 21200:
        return [QgsAuthType.PkiPaths, QgsAuthType.PkiPkcs12, QgsAuthType.IdentityCert]
    else:
        return ["PKI-Paths", "PKI-PKCS#12", "Identity-Cert"]

def getPemPkiPaths(authid, authtype):
    certfile, keyfile, cafile = '', '', ''

    if QGis.QGIS_VERSION_INT < 21200:
        if authtype == QgsAuthType.PkiPaths:
            configpki = QgsAuthConfigPkiPaths()
            QgsAuthManager.instance().loadAuthenticationConfig(authid, configpki, True)
            certfile = _getAsPem(configpki.certId(), configpki.certAsPem())
            if configpki.keyPassphrase():
                keyfile = _saveTempPem(configpki.keyAsPem(False)[0])
            else:
                keyfile = _getAsPem(configpki.keyId(), configpki.keyAsPem(True)[0])
            if QGis.QGIS_VERSION_INT < 20802:
                cafile = _getAsPem(configpki.caCertsId(), configpki.caCertsAsPem())
        elif authtype == QgsAuthType.PkiPkcs12:
            configpki = QgsAuthConfigPkiPkcs12()
            QgsAuthManager.instance().loadAuthenticationConfig(authid, configpki, True)
            keyfile = _saveTempPem(configpki.keyAsPem(False)[0])
            certfile = _saveTempPem(configpki.certAsPem())
            if QGis.QGIS_VERSION_INT < 20802:
                cafile = _saveTempPem(configpki.caCertsAsPem())
        elif QGis.QGIS_VERSION_INT >= 20802 and authtype == QgsAuthType.IdentityCert:
            configpki = QgsAuthConfigIdentityCert()
            QgsAuthManager.instance().loadAuthenticationConfig(authid, configpki, True)
            keyfile = _saveTempPem(configpki.keyAsPem(False)[0])
            certfile = _saveTempPem(configpki.certAsPem())
    else:
        if authtype == "PKI-Paths":
            amcfg = QgsAuthMethodConfig()
            QgsAuthManager.instance().loadAuthenticationConfig(authid, amcfg, True)
            if amcfg.isValid():
                bundle = QgsAuthCertUtils.certKeyBundleToPem(
                    amcfg.config('certpath'),
                    amcfg.config('keypath'),
                    amcfg.config('keypass'),
                    False)
                if len(bundle) > 1:
                    certfile = _saveTempPem(bundle[0])
                    keyfile = _saveTempPem(bundle[1])
        elif authtype == 'PKI-PKCS#12':
            amcfg = QgsAuthMethodConfig()
            QgsAuthManager.instance().loadAuthenticationConfig(authid, amcfg, True)
            if amcfg.isValid():
                bundle = QgsAuthCertUtils.pkcs12BundleToPem(
                    amcfg.config('bundlepath'),
                    amcfg.config('bundlepass'),
                    False)
                if len(bundle) > 1:
                    certfile = _saveTempPem(bundle[0])
                    keyfile = _saveTempPem(bundle[1])
        elif authtype == 'Identity-Cert':
            amcfg = QgsAuthMethodConfig()
            QgsAuthManager.instance().loadAuthenticationConfig(authid, amcfg, True)
            if amcfg.isValid():
                bundle = QgsAuthManager.instance().getCertIdentityBundleToPem(
                    amcfg.config('certid'))
                if len(bundle) > 1:
                    certfile = _saveTempPem(bundle[0])
                    keyfile = _saveTempPem(bundle[1])

    if QGis.QGIS_VERSION_INT >= 20802:
        cafile = _saveTempPem(QgsAuthManager.instance().getTrustedCaCertsPemText())

    return certfile, keyfile, cafile

def _getAsPem(filename, pemString):
    if filename and os.path.splitext(filename)[0].lower() != ".pem":
        return _saveTempPem(pemString)
    return filename

def _saveTempPem(pemString):
    filename = os.path.join(certFolder(), str(uuid.uuid4()) + ".pem")
    with open(filename,'w') as f:
        f.write(pemString)
    return filename

def removePkiTempFiles(catalogs):
    for catalog in catalogs.values():
        removeCatalogPkiTempFiles(catalog)

def removeCatalogPkiTempFiles(catalog):
    if isinstance(catalog, PKICatalog):
        if catalog.cert.startswith(TEMP_CERT_FILE_PREFIX):
            os.remove(catalog.certfile)
        if catalog.key.startswith(TEMP_CERT_FILE_PREFIX):
            os.remove(catalog.keyfile)
        if catalog.ca_cert.startswith(TEMP_CERT_FILE_PREFIX):
            os.remove(catalog.cafile)



