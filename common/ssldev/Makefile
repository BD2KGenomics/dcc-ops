NAME=redwood.io

ARTIFACTS=artifacts

KEY=${NAME}.key
CSR=${NAME}.csr
CRT=${NAME}.crt
TRUST=cacerts

PASSWORD=password
TRUST_PASSWORD=password


all: crt trust

crt: ${ARTIFACTS}/${CRT}
${ARTIFACTS}/${CRT}: ${ARTIFACTS}/${CSR}
	openssl x509 -signkey ${ARTIFACTS}/${KEY} -in ${ARTIFACTS}/${CSR} -req -days 365 -out ${ARTIFACTS}/${CRT} -extfile openssl-cgl.cfg -extensions v3_req

csr: ${ARTIFACTS}/${CSR}
${ARTIFACTS}/${CSR}: ${ARTIFACTS}
	openssl req -new -out ${ARTIFACTS}/${CSR} -newkey rsa:4096 -nodes -keyout ${ARTIFACTS}/${KEY} -config openssl-cgl.cfg

${ARTIFACTS}:
	mkdir -p ${ARTIFACTS}

clean:
	- rm -r ${ARTIFACTS}

view_csr: ${ARTIFACTS}/${CSR}
	openssl req -text -noout -verify -in ${ARTIFACTS}/${CSR}

view_crt: ${ARTIFACTS}/${CRT}
	openssl x509 -text -noout -in ${ARTIFACTS}/${CRT}

${ARTIFACTS}/${TRUST}: trust
trust: ${ARTIFACTS}/${CRT} cacerts.raw ${ARTIFACTS}
	cp cacerts.raw ${ARTIFACTS}/${TRUST}
	keytool -import -noprompt -trustcacerts -keystore ${ARTIFACTS}/${TRUST} -storepass changeit -alias ${NAME} -file ${ARTIFACTS}/${CRT}
	keytool -storepasswd -keystore ${ARTIFACTS}/${TRUST} -storepass changeit -new ${TRUST_PASSWORD}
