NAME=storage.ucsc-cgl.org

ARTIFACTS=artifacts

KEY=${NAME}.key
CSR=${NAME}.csr
CRT=${NAME}.crt
PKCS12=${NAME}.p12
JKS=${NAME}.jks
SERVER_TRUST=cacerts
CLIENT_TRUST=clientcacerts

SERVER_BUNDLE=serverssl.tar.gz
CLIENT_BUNDLE=clientssl.tar.gz

PASSWORD=password
SERVER_TRUST_PASSWORD=password



all: server client

server: ${ARTIFACTS}/${SERVER_BUNDLE}

${ARTIFACTS}/${SERVER_BUNDLE}: ${ARTIFACTS}/${JKS} ${ARTIFACTS}/${PKCS12} ${ARTIFACTS}/${CLIENT_TRUST}
	tar czfC ${ARTIFACTS}/${SERVER_BUNDLE} ${ARTIFACTS} ${JKS} ${PKCS12} ${SERVER_TRUST}

client: ${ARTIFACTS}/${CLIENT_BUNDLE}

${ARTIFACTS}/${CLIENT_BUNDLE}: ${ARTIFACTS}/${CLIENT_TRUST}
	tar czfC ${ARTIFACTS}/${CLIENT_BUNDLE} ${ARTIFACTS} ${CLIENT_TRUST}

jks: ${ARTIFACTS}/${JKS}

${ARTIFACTS}/${JKS}: ${ARTIFACTS}/${PKCS12}
	keytool -importkeystore -srckeystore ${ARTIFACTS}/${PKCS12} -srcstoretype pkcs12 -srcstorepass ${PASSWORD} -destkeystore ${ARTIFACTS}/${JKS} -deststoretype jks -deststorepass ${PASSWORD}

pkcs12: ${ARTIFACTS}/${PKCS12}

${ARTIFACTS}/${PKCS12}: ${ARTIFACTS}/${CRT}
	openssl pkcs12 -inkey ${ARTIFACTS}/${KEY} -passin pass:${PASSWORD} -in ${ARTIFACTS}/${CRT} -export -out ${ARTIFACTS}/${PKCS12}  -passout pass:${PASSWORD}

crt: ${ARTIFACTS}/${CRT}

${ARTIFACTS}/${CRT}: ${ARTIFACTS}/${CSR}
	openssl x509 -signkey ${ARTIFACTS}/${KEY} -passin pass:${PASSWORD} -in ${ARTIFACTS}/${CSR} -req -days 365 -out ${ARTIFACTS}/${CRT} -extfile openssl-cgl.cfg -extensions v3_req

csr: ${ARTIFACTS}/${CSR}

${ARTIFACTS}/${CSR}: ${ARTIFACTS}
	openssl req -new -out ${ARTIFACTS}/${CSR} -newkey rsa:4096 -keyout ${ARTIFACTS}/${KEY} -passout pass:${PASSWORD} -config openssl-cgl.cfg

${ARTIFACTS}:
	mkdir -p ${ARTIFACTS}

clean:
	- rm -r ${ARTIFACTS}

view_csr: ${ARTIFACTS}/${CSR}
	openssl req -text -noout -verify -in ${ARTIFACTS}/${CSR}

view_crt: ${ARTIFACTS}/${CRT}
	openssl x509 -text -noout -in ${ARTIFACTS}/${CRT}

view_pkcs12: ${ARTIFACTS}/${PKCS12}
	keytool -list -keystore ${ARTIFACTS}/${PKCS12} -storepass ${PASSWORD} -storetype pkcs12 -v

view_jks: ${ARTIFACTS}/${JKS}
	keytool -list -keystore ${ARTIFACTS}/${JKS} -storepass ${PASSWORD} -v

${ARTIFACTS}/${SERVER_TRUST}: trust

${ARTIFACTS}/${CLIENT_TRUST}: trust

trust: ${ARTIFACTS}/${CRT} cacerts.raw artifacts
	cp cacerts.raw ${ARTIFACTS}/${CLIENT_TRUST}
	keytool -import -noprompt -trustcacerts -keystore ${ARTIFACTS}/${CLIENT_TRUST} -storepass changeit -alias ${NAME} -file ${ARTIFACTS}/${CRT}
	cp ${ARTIFACTS}/${CLIENT_TRUST} ${ARTIFACTS}/${SERVER_TRUST}
	keytool -storepasswd -keystore ${ARTIFACTS}/${SERVER_TRUST} -storepass changeit -new ${SERVER_TRUST_PASSWORD}
