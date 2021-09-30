# Cloudnative Website with Autoscaling
Deploy Cloud Native Website on OKE with autoscaling capability

## Install Metrics Server to OKE cluster
```
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```
## Install Nginx Ingress Controller using Helm
1. Add ingress-nginx repo
```
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
```
2. Update helm repo
```
helm repo update
```
3. Create ingress-nginx namespace
```
kubectl create namespace ingress-nginx
```
4. Install nginx ingress controller
```
helm install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx --version 3.34.0 --set rbac.create=true --set controller.service.annotations."service\.beta\.kubernetes\.io/oci-load-balancer-protocol"=TCP
```
5. Find out public IP of nginx ingress controller
```
kubectl get svc ingress-nginx-controller -n ingress-nginx
```

## Install Kubernetes Dashboard using Helm
1. Add kubernetes-dashboard repo
```
helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard
```
2. Update helm repo
```
helm repo update
```
3. Install Kubernetes Dashboard
```
helm install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard --namespace kube-system --set ingress.enabled=true --set ingress.hosts='{dashboard.kube-system.<External IP>.nip.io}' --version 4.3.1
```
* change the `<External IP>` to the ingress controller public IP.

4. Create dashboard user to access the dashboard
* Create a manifest yaml file and give it a name. Eg. dashboard-access.yml with the content below:
```yaml
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dashboard-user
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: dashboard-user-role-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: dashboard-user
  namespace: kube-system
```
* Get token of the newly created user
```
kubectl -n kube-system describe secret `kubectl -n kube-system get secret | grep dashboard-user | awk '{print $1}'`
```
* Copy the content of the token

5. Access the dashboard in the browser by inserting the url `https://dashboard.kube-system.<External IP>.nip.io`. Change the `<External IP>` accordingly

6. Select Token in the sign in page and past the token.

## Steps to set up Cluster Autoscaler
 1. Create compartment level dynamic group
 ```
 ALL {instance.compartment.id = '<compartment-ocid>'}
 ```
 2. Create policy needed for autoscaler
 ```
 Allow dynamic-group <DG name> to manage all-resources in compartment <compartment name>
 ```
 3. Create and apply cluster-autoscaler.yml
 * Change line 141 to the appropriate image. Refer to this [link](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengusingclusterautoscaler.htm#unique_1751637304)
 ```
 - image: <image location>/oracle/oci-cluster-autoscaler:<image tag>
 ```
 * Change line 156 to define the required min and max nodes, and the node pool OCID
 ```
 - --nodes=<min node>:<max node>:<node pool OCID>
 ```
 * Apply this to OKE cluster
 ```
 kubectl apply -f cluster-autoscaler.yml
 ```
 4. Identify which Cluster Autoscaler pod is currently performing the actions
 ```
 kubectl get lease cluster-autoscaler -n kube-system
 ```
 5. Check the logs of the cluster autoscaler
 ```
 kubectl logs --tail=20 pod/<pod name obtained from step 4> -n kube-system
 ```
 
## Steps to set up Horizontal Pod Autoscaler
1. Create Horizontal Pod Autoscaler (HPA) for the deployment
* Create manifest yaml file for HPA and give it a name. Eg. hpa_nginx.yml
* Insert the content below
```yaml
apiVersion: autoscaling/v1
kind: HorizontalPodAutoscaler
metadata:
  name: <hpa name>
  namespace: <namespace>
spec:
  maxReplicas: <max pods>
  minReplicas: <mind pods>
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: <deployment name>
  targetCPUUtilizationPercentage: <cpu utilization target>
```
Example
```yaml
apiVersion: autoscaling/v1
kind: HorizontalPodAutoscaler
metadata:
  name: nginx
  namespace: cloudnative-webapp-adb
spec:
  maxReplicas: 20
  minReplicas: 3
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nginx
  targetCPUUtilizationPercentage: 20
  ```
  * Apply to OKE cluster
  ```
  kubectl apply -f hpa_nginx.yml
  ```
  
2. Check HPA status
```
kubectl get hpa
```
Example output
```
NAME    REFERENCE          TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
nginx   Deployment/nginx   0%/20%    3         20        3          60m
php     Deployment/php     0%/20%    3         20        3          27m
```
3. Check the status and events of the HPA
```
kubectl describe hpa/<deployment name>
```

## Steps to set up K6 Load Tester
1. Provision VCN, public subnet and IGW.
2. Configure the appropriate route rules and security list.
3. Provision an Oracle Linux instance with at least 2 OCPU and 16GB memory.
4. SSH to the instance.
5. Install K6
```
wget https://github.com/grafana/k6/releases/download/v0.33.0/k6-v0.33.0-linux-amd64.rpm
yum localinstall k6-v0.33.0-linux-amd64.rpm -y
```
6. Create a load test config javascript file and give it a name. Eg. script.js
7. Insert the content below to the file
```javascript
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  vus: <number of virtual users>,
  duration: '<duration in second>',
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95 percent of response times must be below 500ms
    http_req_failed: ['rate<0.01'], // http errors should be less than 1%
  },
};

export default function () {
    let res = http.get('<url to be tested>');
    check (res, {
        'HTTP 200 OK': (r) => r.status == 200,
    });
}
```
**Example**

```javascript
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  vus: 50,
  duration: '300s',
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95 percent of response times must be below 500ms
    http_req_failed: ['rate<0.01'], // http errors should be less than 1%
  },
};

export default function () {
    let res = http.get('https://google.com');
    check (res, {
        'HTTP 200 OK': (r) => r.status == 200,
    });
}

```
8. Run the load test
```
k6 run script.js
```

## Verify pod and node autoscaling
1. Check pods autoscaling
```
watch -n 2 kubectl get pods
```
2. Check hpa events
```
kubectl describe hpa/<deployment name>
```
3. Check nodes autoscaling
* Check from OCI web console -> navigate to OKE node pool
* Check the logs of node autoscaler as stated in step 4 and 5 of [Steps to set up Cluster Autoscaler](#steps-to-set-up-cluster-autoscaler)



