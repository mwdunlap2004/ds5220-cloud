output "instance_name" {
  description = "Name of the compute instance"
  value       = google_compute_instance.main.name
}

output "instance_internal_ip" {
  description = "Internal IP address of the compute instance"
  value       = google_compute_instance.main.network_interface[0].network_ip
}

output "instance_external_ip" {
  description = "External (public) IP address of the compute instance"
  value       = google_compute_instance.main.network_interface[0].access_config[0].nat_ip
}

output "instance_self_link" {
  description = "Self link of the compute instance"
  value       = google_compute_instance.main.self_link
}

output "bucket_name" {
  description = "Name of the GCS bucket"
  value       = google_storage_bucket.main.name
}

output "bucket_url" {
  description = "The base URL of the GCS bucket"
  value       = google_storage_bucket.main.url
}
