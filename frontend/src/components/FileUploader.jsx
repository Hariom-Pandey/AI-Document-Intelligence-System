import React, { useState, useRef } from "react";
import { UploadCloud, File, AlertCircle, CheckCircle, Loader2 } from "lucide-react";
import { api } from "../services/api";

export default function FileUploader({ onUploadSuccess }) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const fileInputRef = useRef(null);

  const allowedExtensions = [".pdf", ".docx", ".txt"];

  const validateFile = (selectedFile) => {
    setError(null);
    setSuccess(null);
    if (!selectedFile) return false;

    const ext = "." + selectedFile.name.split(".").pop().toLowerCase();
    if (!allowedExtensions.includes(ext)) {
      setError(`Invalid file type (${ext}). Supported formats: PDF, DOCX, TXT.`);
      return false;
    }

    // 50MB limit
    if (selectedFile.size > 50 * 1024 * 1024) {
      setError("File exceeds maximum allowed size of 50 MB.");
      return false;
    }

    return true;
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        setFile(droppedFile);
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (validateFile(selected)) {
        setFile(selected);
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const res = await api.uploadDocument(file);
      setSuccess(`Document uploaded successfully! Processing pipeline initiated.`);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      if (onUploadSuccess) onUploadSuccess(res);
    } catch (err) {
      setError(err.message || "Failed to upload document.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="uploader-card">
      <div
        className={`dropzone ${isDragging ? "active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleFileChange}
          style={{ display: "none" }}
        />
        <div className="dropzone-content">
          <div className="upload-icon-wrapper">
            <UploadCloud size={36} className="upload-icon" />
          </div>
          <h3>Choose a document or drag it here</h3>
          <p className="dropzone-sub">Supports PDF, DOCX, and TXT files up to 50MB</p>
          <span className="browse-badge">Browse File</span>
        </div>
      </div>

      {file && (
        <div className="selected-file-banner">
          <div className="file-info">
            <File size={22} className="file-badge-icon" />
            <div>
              <p className="filename">{file.name}</p>
              <p className="filesize">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
            </div>
          </div>
          <button
            className="btn btn-primary"
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? (
              <>
                <Loader2 size={16} className="animate-spin" /> Uploading & Processing...
              </>
            ) : (
              "Process Document"
            )}
          </button>
        </div>
      )}

      {error && (
        <div className="alert alert-error">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          <CheckCircle size={18} />
          <span>{success}</span>
        </div>
      )}
    </div>
  );
}

