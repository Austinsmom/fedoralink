from rdflib import Namespace, URIRef

NAMESPACES = {
            "premis"        :   "http://www.loc.gov/premis/rdf/v1#",
            "image"         :   "http://www.modeshape.org/images/1.0",
            "sv"            :   "http://www.jcp.org/jcr/sv/1.0",
            "test"          :   "info:fedora/test/",
            "nt"            :   "http://www.jcp.org/jcr/nt/1.0",
            "rdfs"          :   "http://www.w3.org/2000/01/rdf-schema#",
            "xsi"           :   "http://www.w3.org/2001/XMLSchema-instance",
            "mode"          :   "http://www.modeshape.org/1.0",
            "rdf"           :   "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "fedora"        :   "http://fedora.info/definitions/v4/repository#",
            "fedora_index"  :   "http://fedora.info/definitions/v4/indexing#",
            "xml"           :   "http://www.w3.org/XML/1998/namespace",
            "ebucore"       :   "http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#",
            "ldp"           :   "http://www.w3.org/ns/ldp#",
            "xs"            :   "http://www.w3.org/2001/XMLSchema",
            "fedoraconfig"  :   "http://fedora.info/definitions/v4/config#",
            "mix"           :   "http://www.jcp.org/jcr/mix/1.0",
            "foaf"          :   "http://xmlns.com/foaf/0.1/",
            "dc"            :   "http://purl.org/dc/elements/1.1/",
            "dcterms"       :   "http://purl.org/dc/terms/",
            "cis"           :   "http://cis.vscht.cz/ns/repository#",
            "cesnet"        :   "http://cesnet.cz/ns/repository#",
            "cesnet_state"  :   "http://cesnet.cz/ns/repository/state#",
            "cesnet_type"  :   "http://cesnet.cz/ns/repository/type#",
            "acl"           :   "http://www.w3.org/ns/auth/acl#"
}

FEDORA          =   Namespace(NAMESPACES['fedora'])
FEDORA_INDEX    =   Namespace(NAMESPACES['fedora_index'])
FEDORA_CREATED_METADATA = URIRef(FEDORA.created)
FEDORA_LAST_MODIFIED_BY_METADATA = URIRef(FEDORA.lastModifiedBy)
FEDORA_PRIMARY_TYPE_METADATA = URIRef(FEDORA.primaryType)
FEDORA_MIXIN_TYPES_METADATA = URIRef(FEDORA.mixinTypes)
FEDORA_LAST_MODIFIED_METADATA = URIRef(FEDORA.lastModified)

RDF             =   Namespace(NAMESPACES['rdf'])
RDFS            =   Namespace(NAMESPACES['rdfs'])
LDP             =   Namespace(NAMESPACES['ldp'])

EBUCORE         =   Namespace(NAMESPACES['ebucore'])
PREMIS          =   Namespace(NAMESPACES['premis'])

CIS             =   Namespace(NAMESPACES['cis'])
CESNET          =   Namespace(NAMESPACES['cesnet'])
CESNET_STATE    =   Namespace(NAMESPACES['cesnet_state'])
CESNET_TYPE     =   Namespace(NAMESPACES['cesnet_type'])
ACL             =   Namespace(NAMESPACES['acl'])




