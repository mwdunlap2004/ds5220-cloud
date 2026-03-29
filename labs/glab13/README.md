# Graduate Lab: Running Kubernetes Locally with a Kafka Cluster

Note: This is the third of five graduate labs.

**Estimated time:** 45-60 minutes

---

## 1. Introduction

Kubernetes (K8s) is the industry-standard platform for orchestrating containerized workloads.
In production, data engineering teams run stream-processing systems like Apache Kafka,
Spark clusters, and ML serving infrastructure on Kubernetes. In this lab you will:

1. Stand up a **local Kubernetes cluster** on your laptop.
2. Learn the core `kubectl` commands for inspecting cluster resources.
3. Deploy a **3-broker Apache Kafka cluster** (using KRaft mode — no ZooKeeper required).
4. Deploy the **Redpanda Console** web UI to visually manage your Kafka cluster.
5. Use **port-forwarding** to access the web UI from your browser.

### Why Kafka?

Apache Kafka is a distributed event-streaming platform used in virtually every modern
data pipeline. It powers real-time analytics, change-data-capture, feature stores, and
more. Running a multi-broker Kafka cluster on Kubernetes demonstrates real-world
patterns — StatefulSets, headless Services, ConfigMaps — that you will encounter in
production data infrastructure.

---

## 2. Prerequisites

You need **one** of the following installed on your machine:

| Option | Install Link | Notes |
|--------|-------------|-------|
| **Docker Desktop** (with built-in Kubernetes) | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) | macOS, Windows, Linux. Kubernetes is a checkbox in Settings. |
| **Minikube** | [minikube.sigs.k8s.io/docs/start](https://minikube.sigs.k8s.io/docs/start/) | Requires Docker (or another driver) as a backend. |

You also need `kubectl`, the Kubernetes command-line tool:

```bash
# macOS (Homebrew)
brew install kubectl

# Or, if using Docker Desktop, kubectl is already bundled.
# Verify:
kubectl version --client
```

### Resource Requirements

This lab runs three Kafka brokers and a web console. Ensure your Docker environment
has at least **4 GB of memory** and **2 CPUs** allocated (check Docker Desktop
Settings > Resources).

---

## 3. Start Your Local Cluster

Choose **one** of the two options below.

### Option A: Docker Desktop

1. Open **Docker Desktop**.
2. Go to **Settings > Kubernetes**.
3. Check **Enable Kubernetes** and click **Apply & Restart**.
4. Wait for the Kubernetes status indicator (bottom-left) to turn green.

### Option B: Minikube

```bash
# Start a cluster with sufficient resources
minikube start --cpus=2 --memory=4096

# Verify it is running
minikube status
```

### Verify Your Cluster

Regardless of which option you chose, run:

```bash
kubectl cluster-info
```

You should see output showing the Kubernetes control plane address. If you see an
error, revisit the setup steps above.

---

## 4. Exploring Your Cluster with `kubectl`

Before deploying anything, let's explore the cluster that is already running.

### 4.1 Nodes

A **node** is a machine (physical or virtual) in the cluster. In a local setup, you
have a single node.

```bash
kubectl get nodes
```

Try the "wide" output to see more detail:

```bash
kubectl get nodes -o wide
```

### 4.2 Namespaces

**Namespaces** are logical partitions of a cluster — similar to schemas in a database.
Kubernetes ships with several default namespaces:

```bash
kubectl get namespaces
```

You should see at least `default`, `kube-system`, and `kube-public`. The `kube-system`
namespace holds the cluster's own infrastructure components.

### 4.3 Pods in `kube-system`

**Pods** are the smallest deployable unit in Kubernetes — a wrapper around one or more
containers. Let's look at what is already running:

```bash
kubectl get pods -n kube-system
```

You will see core components like `coredns`, `etcd`, `kube-apiserver`, `kube-scheduler`,
and others that make up the Kubernetes control plane.

### 4.4 All Resources

You can ask Kubernetes for *everything* in a namespace at once:

```bash
kubectl get all -n kube-system
```

### 4.5 Describing a Resource

The `describe` command gives verbose detail about any resource. Pick a pod from the
previous output and examine it:

```bash
# Replace <pod-name> with an actual pod name from the output above
kubectl describe pod <pod-name> -n kube-system
```

Look for the **Events** section at the bottom — this is where Kubernetes logs
scheduling decisions, image pulls, and container starts.

### 4.6 Quick Reference

| Command | Purpose |
|---------|---------|
| `kubectl get nodes` | List cluster nodes |
| `kubectl get namespaces` | List all namespaces |
| `kubectl get pods -n <ns>` | List pods in a namespace |
| `kubectl get all -n <ns>` | List all resources in a namespace |
| `kubectl describe <type> <name> -n <ns>` | Detailed info about a resource |
| `kubectl logs <pod> -n <ns>` | View container logs |
| `kubectl get events -n <ns>` | View recent cluster events |

---

## 5. Deploy a Kafka Cluster

Now we will deploy a real distributed system. The YAML spec files have been provided
for you in this lab directory. Take a moment to open each file and read through the
comments before applying them.

### 5.1 Understand the Architecture

Our deployment consists of four Kubernetes resource types:

| Resource | Kind | Purpose |
|----------|------|---------|
| `kafka-namespace.yaml` | Namespace | Isolates all Kafka resources |
| `kafka-cluster.yaml` | ConfigMap, StatefulSet, Services | Three Kafka brokers in KRaft mode |
| `redpanda-console.yaml` | ConfigMap, Deployment, Service | Web UI for Kafka management |

**Key Kubernetes concepts in play:**

- **StatefulSet** — like a Deployment, but gives each pod a stable hostname
  (`kafka-0`, `kafka-1`, `kafka-2`). This is essential for distributed systems where
  nodes must find each other by name.
- **Headless Service** (`clusterIP: None`) — allows DNS lookups to resolve directly to
  individual pod IPs instead of load-balancing across them.
- **ConfigMap** — injects configuration data into pods as environment variables or
  mounted files.

### 5.2 Create the Namespace

```bash
kubectl apply -f kafka-namespace.yaml
```

Verify it exists:

```bash
kubectl get namespaces
```

You should now see `kafka` in the list.

### 5.3 Deploy the Kafka Brokers

```bash
kubectl apply -f kafka-cluster.yaml
```

This creates a 3-replica StatefulSet. Watch the pods come up:

```bash
kubectl get pods -n kafka -w
```

Wait until all three pods (`kafka-0`, `kafka-1`, `kafka-2`) show `1/1 Running` and
`READY`. This may take 1-3 minutes as the Kafka container image is pulled and the
brokers initialize. Press `Ctrl+C` to stop watching.

> **Troubleshooting:** If a pod is stuck in `Pending` or `CrashLoopBackOff`, use
> `kubectl describe pod kafka-0 -n kafka` and `kubectl logs kafka-0 -n kafka` to
> diagnose the issue. Common causes are insufficient memory or CPU.

### 5.4 Inspect the Kafka Resources

Now explore what was created:

```bash
# List all resources in the kafka namespace
kubectl get all -n kafka

# Look at the StatefulSet
kubectl describe statefulset kafka -n kafka

# Look at the headless service
kubectl describe service kafka-headless -n kafka

# Examine the ConfigMap
kubectl describe configmap kafka-config -n kafka
```

### 5.5 Deploy the Redpanda Console

```bash
kubectl apply -f redpanda-console.yaml
```

Watch for it to become ready:

```bash
kubectl get pods -n kafka -w
```

Wait for the `redpanda-console-*` pod to reach `1/1 Running`. Press `Ctrl+C` to stop.

### 5.6 Verify the Full Deployment

```bash
kubectl get all -n kafka
```

You should see:
- 3 `kafka-*` pods (from the StatefulSet)
- 1 `redpanda-console-*` pod (from the Deployment)
- The `kafka-headless`, `kafka-bootstrap`, and `redpanda-console` services

---

## 6. Access the Redpanda Console via Port-Forwarding

Kubernetes services are only reachable from *inside* the cluster by default. To access
the web UI from your browser, use `kubectl port-forward`:

```bash
kubectl port-forward svc/redpanda-console 8080:8080 -n kafka
```

Now open your browser and navigate to:

**[http://localhost:8080](http://localhost:8080)**

You should see the Redpanda Console dashboard. Explore the interface — you'll find
sections for **Brokers**, **Topics**, and **Consumer Groups**.

> **Keep this terminal open** — port-forwarding runs in the foreground. Open a **new
> terminal window** for the next section.

> **Note** - In a production system this service would be exposed using an "ingress" resource, which creates a URL endpoint connected to the Redpanda Console.

---

## 7. Interact with Kafka

### 7.1 Create a Topic

We'll use `kubectl exec` to run Kafka CLI tools directly inside a broker pod:

```bash
kubectl exec -it kafka-0 -n kafka -- \
  /opt/kafka/bin/kafka-topics.sh \
    --bootstrap-server kafka-bootstrap.kafka.svc.cluster.local:9092 \
    --create \
    --topic sensor-readings \
    --partitions 3 \
    --replication-factor 3
```

Verify the topic was created:

```bash
kubectl exec -it kafka-0 -n kafka -- \
  /opt/kafka/bin/kafka-topics.sh \
    --bootstrap-server kafka-bootstrap.kafka.svc.cluster.local:9092 \
    --describe \
    --topic sensor-readings
```

You should see that the topic has 3 partitions, each with 3 replicas spread across
brokers 0, 1, and 2. Switch to your browser and refresh the Redpanda Console — the
new topic should appear under **Topics**.

### 7.2 Produce Messages

Open a producer console and send some messages. Type each message and press Enter:

```bash
kubectl exec -it kafka-0 -n kafka -- \
  /opt/kafka/bin/kafka-console-producer.sh \
    --bootstrap-server kafka-bootstrap.kafka.svc.cluster.local:9092 \
    --topic sensor-readings
```

Type a few lines of sample data (press Enter after each):

```
{"sensor_id": "temp-01", "value": 22.5, "unit": "celsius"}
{"sensor_id": "temp-02", "value": 19.8, "unit": "celsius"}
{"sensor_id": "humid-01", "value": 65.2, "unit": "percent"}
{"sensor_id": "temp-01", "value": 23.1, "unit": "celsius"}
{"sensor_id": "pressure-01", "value": 1013.25, "unit": "hPa"}
```

Press `Ctrl+C` to exit the producer.

### 7.3 Consume Messages

Now read those messages back:

```bash
kubectl exec -it kafka-0 -n kafka -- \
  /opt/kafka/bin/kafka-console-consumer.sh \
    --bootstrap-server kafka-bootstrap.kafka.svc.cluster.local:9092 \
    --topic sensor-readings \
    --from-beginning
```

You should see all five messages output to your terminal. Press `Ctrl+C` to exit.

### 7.4 Explore in the Redpanda Console

Go back to [http://localhost:8080](http://localhost:8080) in your browser and:

1. Click on **Topics** > **sensor-readings**.
2. View the **Messages** tab — you should see the JSON messages you produced.
3. Click on **Brokers** to see your 3-broker cluster and resource utilization.

---

## 8. Knowledge Check

1. **StatefulSet vs. Deployment:** Why does Kafka use a StatefulSet instead of a
   Deployment? What would happen if Kafka brokers did not have stable hostnames?
2. **Why Three Nodes?:** Why would a data pipeline service be deployed across three
   nodes in a cluster instead of running on a single node?
3. **Replication:** When you described the `sensor-readings` topic, you saw that each
   partition has 3 replicas. What happens if `kafka-1` crashes — is data lost?
4. **Port-Forwarding:** Why can't you just open `http://redpanda-console.kafka:8080`
   in your browser? What does `kubectl port-forward` actually do?
5. **Storage:** What would happen if you delete the entire stack and re-create it, would topics and messages persist? Why/why not?

---

## 9. Submission

Compile the following into **one PDF** and submit according to your course instructions.

1. **Cluster setup**
   A screenshot of the output of `kubectl cluster-info` and `kubectl get nodes`
   showing your local cluster is running.

2. **Namespace & pod listing**
   A screenshot of `kubectl get all -n kafka` showing all three Kafka brokers and
   the Redpanda Console pod in a Running state.

3. **Topic description**
   A screenshot or copy-paste of the `--describe --topic sensor-readings` output
   showing partitions and replicas.

4. **Redpanda Console**
   A screenshot of the Redpanda Console in your browser showing:
   - The **Brokers** view (3 brokers visible), AND
   - The **Messages** tab for `sensor-readings` with your produced messages visible.

5. **Knowledge Check**
   Brief answers to the five questions in Section 8.

Name your file `glab13-lastname-firstname.pdf` (or as specified by your instructor).

---

## 10. Cleanup

When you are finished, tear down all the resources and stop your cluster:

```bash
# Delete everything in the kafka namespace
kubectl delete namespace kafka

# Verify cleanup
kubectl get all -n kafka
# Should return: "No resources found in kafka namespace."
```

Then stop your local cluster:

```bash
# If using Minikube:
minikube stop

# If using Docker Desktop:
# Go to Settings > Kubernetes > uncheck "Enable Kubernetes" > Apply & Restart
# (or simply leave it running if you prefer)
```

---

## Answer Key

1. **StatefulSet vs. Deployment:** A StatefulSet gives each pod a persistent, ordered identity (`kafka-0`, `kafka-1`, `kafka-2`) that survives restarts. Kafka brokers register with the controller quorum using their node ID and advertised hostname. If a Deployment were used, pod names would be randomized (e.g., `kafka-7f8b9c-x4k2n`), and brokers would not be able to rejoin the cluster with the same identity after a restart.

2. **Why Three Nodes?:** Good answers include high availability (the service can survive a node failure), fault tolerance (workloads can fail over), and better performance/scalability by spreading traffic and storage across machines instead of creating a single point of failure.

3. **Replication:** No data is lost. With a replication factor of 3, every partition has its data stored on all three brokers. If `kafka-1` crashes, the remaining two replicas continue serving reads and writes. The partition leader automatically fails over to one of the in-sync replicas on `kafka-0` or `kafka-2`.

4. **Port-Forwarding:** The service `redpanda-console.kafka` only resolves inside the cluster's internal DNS (CoreDNS). Your laptop is not part of the cluster network. `kubectl port-forward` creates a tunnel — it binds a port on your local machine (`localhost:8080`) and forwards TCP traffic through the Kubernetes API server into the target pod or service inside the cluster.

5. **Storage:** In this lab setup, topics and messages usually do **not** persist after deleting the entire stack, because the Kafka broker storage is tied to Kubernetes resources in the `kafka` namespace. When the namespace and its persistent volumes are deleted, the stored data is removed. (This is known as "ephemeral storage".) Data would persist only if volumes were retained and reattached.
