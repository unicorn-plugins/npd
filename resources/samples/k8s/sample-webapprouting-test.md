apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: test-app
  template:
    metadata:
      labels:
        app: test-app
    spec:
      nodeSelector:
        karpenter.sh/nodepool: service
      securityContext:
        seccompProfile:
          type: RuntimeDefault        # ← seccomp 경고 해결
      containers:
        - name: test-app
          image: nginx:1.27.4         # ← latest 대신 명시적 버전
          resources:
            requests:
              cpu: "1"
              memory: "2Gi"
          livenessProbe:              # ← livenessProbe 추가
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:             # ← readinessProbe 추가
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: test-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  ingressClassName: webapprouting.kubernetes.azure.com
  rules:
    - http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-service
                port:
                  number: 80