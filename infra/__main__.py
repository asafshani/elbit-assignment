import pulumi
import pulumi_kubernetes as k8s

# Load configuration
config = pulumi.Config()
app_name = "jewish-holidays"
container_image = config.get("containerImage") or "jewish-holidays-app:1.0.0"
replicas = config.get_int("replicas") or 2
container_port = 8080

# Create a Secret (demonstrating Pulumi secret management)
app_secret = k8s.core.v1.Secret(
    f"{app_name}-secret",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=f"{app_name}-secret",
    ),
    string_data={
        "API_KEY": config.get_secret("apiKey") or "demo-secret-key-12345",
    },
)

# Create a ConfigMap for application configuration
app_config = k8s.core.v1.ConfigMap(
    f"{app_name}-config",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=f"{app_name}-config",
    ),
    data={
        "APP_ENV": "production",
        "LOG_LEVEL": "info",
    },
)

# Create the Deployment
app_deployment = k8s.apps.v1.Deployment(
    f"{app_name}-deployment",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=app_name,
        labels={"app": app_name},
    ),
    spec=k8s.apps.v1.DeploymentSpecArgs(
        replicas=replicas,
        selector=k8s.meta.v1.LabelSelectorArgs(
            match_labels={"app": app_name},
        ),
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(
                labels={"app": app_name},
            ),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[
                    k8s.core.v1.ContainerArgs(
                        name=app_name,
                        image=container_image,
                        image_pull_policy="Never",  # Use local image from Minikube
                        ports=[
                            k8s.core.v1.ContainerPortArgs(
                                container_port=container_port,
                            ),
                        ],
                        env_from=[
                            # Load environment variables from ConfigMap
                            k8s.core.v1.EnvFromSourceArgs(
                                config_map_ref=k8s.core.v1.ConfigMapEnvSourceArgs(
                                    name=f"{app_name}-config",
                                ),
                            ),
                            # Load secrets as environment variables
                            k8s.core.v1.EnvFromSourceArgs(
                                secret_ref=k8s.core.v1.SecretEnvSourceArgs(
                                    name=f"{app_name}-secret",
                                ),
                            ),
                        ],
                        resources=k8s.core.v1.ResourceRequirementsArgs(
                            requests={
                                "cpu": config.get("cpuRequest") or "100m",
                                "memory": config.get("memoryRequest") or "128Mi",
                            },
                            limits={
                                "cpu": config.get("cpuLimit") or "250m",
                                "memory": config.get("memoryLimit") or "256Mi",
                            },
                        ),
                        liveness_probe=k8s.core.v1.ProbeArgs(
                            http_get=k8s.core.v1.HTTPGetActionArgs(
                                path="/health",
                                port=container_port,
                            ),
                            initial_delay_seconds=10,
                            period_seconds=30,
                        ),
                        readiness_probe=k8s.core.v1.ProbeArgs(
                            http_get=k8s.core.v1.HTTPGetActionArgs(
                                path="/health",
                                port=container_port,
                            ),
                            initial_delay_seconds=5,
                            period_seconds=10,
                        ),
                    ),
                ],
            ),
        ),
    ),
)

# Create a Service to expose the application
app_service = k8s.core.v1.Service(
    f"{app_name}-service",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=f"{app_name}-service",
        labels={"app": app_name},
    ),
    spec=k8s.core.v1.ServiceSpecArgs(
        type="ClusterIP",
        selector={"app": app_name},
        ports=[
            k8s.core.v1.ServicePortArgs(
                port=80,
                target_port=container_port,
                protocol="TCP",
            ),
        ],
    ),
)

# Create Ingress to expose the application externally with TLS
app_ingress = k8s.networking.v1.Ingress(
    f"{app_name}-ingress",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=f"{app_name}-ingress",
        annotations={
            "nginx.ingress.kubernetes.io/rewrite-target": "/",
            "nginx.ingress.kubernetes.io/ssl-redirect": "true",
        },
    ),
    spec=k8s.networking.v1.IngressSpecArgs(
        ingress_class_name="nginx",
        tls=[
            k8s.networking.v1.IngressTLSArgs(
                hosts=["jewish-holidays.local"],
                secret_name="jewish-holidays-tls",
            ),
        ],
        rules=[
            k8s.networking.v1.IngressRuleArgs(
                host="jewish-holidays.local",
                http=k8s.networking.v1.HTTPIngressRuleValueArgs(
                    paths=[
                        k8s.networking.v1.HTTPIngressPathArgs(
                            path="/",
                            path_type="Prefix",
                            backend=k8s.networking.v1.IngressBackendArgs(
                                service=k8s.networking.v1.IngressServiceBackendArgs(
                                    name=f"{app_name}-service",
                                    port=k8s.networking.v1.ServiceBackendPortArgs(
                                        number=80,
                                    ),
                                ),
                            ),
                        ),
                    ],
                ),
            ),
        ],
    ),
)

# Stack outputs
pulumi.export("app_name", app_name)
pulumi.export("deployment_name", app_deployment.metadata.name)
pulumi.export("service_name", app_service.metadata.name)
pulumi.export("ingress_name", app_ingress.metadata.name)
pulumi.export("container_image", container_image)
pulumi.export("replicas", replicas)