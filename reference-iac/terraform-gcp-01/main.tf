# ----------------------------------------
# Firewall Rules (GCP's equivalent of security groups)
# ----------------------------------------

resource "google_compute_firewall" "allow_ssh" {
  name    = "${var.instance_name}-allow-ssh"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = var.allowed_ssh_cidrs
  target_tags   = ["${var.instance_name}-server"]

  description = "Allow SSH access to the instance"
}

resource "google_compute_firewall" "allow_http" {
  name    = "${var.instance_name}-allow-http"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = var.allowed_http_cidrs
  target_tags   = ["${var.instance_name}-server"]

  description = "Allow HTTP/HTTPS access to the instance"
}

# ----------------------------------------
# Compute Instance
# ----------------------------------------

resource "google_compute_instance" "main" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  tags = ["${var.instance_name}-server"]

  boot_disk {
    initialize_params {
      image = var.image
    }
  }

  network_interface {
    network = "default"

    # Assigns an ephemeral public IP — remove this block for private-only
    access_config {}
  }

  metadata = merge(
    { enable-oslogin = "TRUE" }
  )

  metadata_startup_script = file("startup.sh")

  labels = {
    environment = "dev"
    managed-by  = "terraform"
  }
}

# ----------------------------------------
# GCS Storage Bucket
# ----------------------------------------

resource "google_storage_bucket" "main" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  labels = {
    environment = "dev"
    managed-by  = "terraform"
  }
}
