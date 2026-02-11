{{- /*
Return the standard Postgres environment variables.
*/ -}}
{{- define "api.postgresEnv" -}}
- name: POSTGRES_HOST
  value: {{ printf "%s-postgresql" .Release.Name }}
- name: POSTGRES_PORT
  {{- $port := or (index .Values "global" "postgresql" "service" "ports" "postgresql") (index .Values "postgresql" "primary" "service" "ports" "postgresql") 5432 }}
  value: {{ $port }}
- name: POSTGRES_DATABASE
  {{- $db := or (index .Values "global" "postgresql" "auth" "database") (index .Values "postgresql" "auth" "database")  }}
  value: {{ $db }}
- name: POSTGRES_USER
  {{- $user := or (index .Values "global" "postgresql" "auth" "username") (index .Values "postgresql" "auth" "username") }}
  value: {{ $user }}
- name: POSTGRES_PASSWORD
  {{- $secret := or (index .Values "global" "postgresql" "auth" "existingSecret") (index .Values "postgresql" "auth" "existingSecret") }}
  {{- $password := or (index .Values "global" "postgresql" "auth" "password") (index .Values "postgresql" "auth" "password") }}
  {{- if $secret }}
  valueFrom:
    secretKeyRef:
      name: {{ .Values.postgresql.auth.existingSecret }}
      key: password
  {{- else }}
  value: {{ $password }}
  {{ end }}
{{- end -}}
