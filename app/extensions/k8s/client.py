import time

from kubernetes import client, config

import logging

MAX_RETRIES = 5
SLEEP_INTERVAL = 2

logger = logging.getLogger(__name__)

class K8sClient:
    def __init__(self):
        try:
            # Try to load in-cluster config first
            config.load_incluster_config()
        except config.ConfigException:
            # Fall back to kubeconfig
            config.load_kube_config()

        self.custom_api = client.CustomObjectsApi()
        self.core_api = client.CoreV1Api()

    def get_service_nodeport(self, user, challenge_id, namespace="default"):
        """Get NodePort from the service using the correct service name pattern"""
        try:
            # Using the correct service name pattern
            service_name = f"svc-{user}-{challenge_id}"
            logger.info(f"Looking for service: {service_name}")

            service = self.core_api.read_namespaced_service(
                name=service_name,
                namespace=namespace
            )

            # Get NodePort from service
            if service.spec.ports:
                nodeport = service.spec.ports[0].node_port
                logger.info(f"Found NodePort {nodeport} for service {service_name}")
                return nodeport

            logger.warning(f"No ports found for service {service_name}")
            return None

        except client.rest.ApiException as e:
            if e.status == 404:
                logger.warning(f"Service {service_name} not found yet")
            else:
                logger.error(f"Error getting service {service_name}: {str(e)}")
            return None

    def create_challenge_resource(self, challenge_id, user, namespace="default"):
        """Create a Challenge Custom Resource and wait for service NodePort"""

        logger.info(f"Creating challenge for user {user} with id {challenge_id}")

        # Create the Challenge manifest
        challenge_manifest = {
            "apiVersion": "apps.hexactf.io/v1alpha1",
            "kind": "Challenge",
            "metadata": {
                "name": f"challenge-{challenge_id}-{user}",
                "labels": {
                    "hexactf.io/problemId": str(challenge_id),
                    "hexactf.io/user": user
                }
            },
            "spec": {
                # Add any additional spec fields required
                "namespace":"default",
                "cTemplate": "ubuntu"
            }
        }

        # Create the CR
        response = self.custom_api.create_namespaced_custom_object(
            group="apps.hexactf.io",
            version="v1alpha1",
            namespace=namespace,
            plural="challenges",
            body=challenge_manifest
        )

        logger.info("Challenge CR created, waiting for service...")

        # Wait for the service and NodePort to be assigned
        MAX_RETRIES = 30
        SLEEP_INTERVAL = 2

        for attempt in range(MAX_RETRIES):
            logger.debug(f"Attempt {attempt + 1}/{MAX_RETRIES} to get service NodePort")

            # Check CR status
            cr_status = self.custom_api.get_namespaced_custom_object(
                group="apps.hexactf.io",
                version="v1alpha1",
                namespace=namespace,
                plural="challenges",
                name=f"challenge-{challenge_id}-{user}"
            )

            # Get NodePort from service
            nodeport = self.get_service_nodeport(user, challenge_id, namespace)

            if nodeport:
                logger.info(f"Challenge ready with NodePort {nodeport}")
                return {
                    'challenge': {
                        'host': 'localhost',  # Can be configured based on environment
                        'port': nodeport,
                        'status': cr_status.get('status', {}).get('phase', 'Unknown')
                    }
                }

            logger.debug(f"Service/NodePort not ready yet, waiting...")
            time.sleep(SLEEP_INTERVAL)

        raise TimeoutError(f"Timeout waiting for service svc-{user}-{challenge_id}")



