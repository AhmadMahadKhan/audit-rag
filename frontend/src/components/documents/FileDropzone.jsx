import React, { useState, useRef } from 'react';
import { UploadCloud, File, CheckCircle, AlertCircle } from 'lucide-react';
import Spinner from '../common/Spinner';

export const FileDropzone = ({ onUpload, isUploading }) => {
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFiles = (files) => {
    if (files && files.length > 0) {
      onUpload(Array.from(files));
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
      style={{
        border: `2px dashed ${dragOver ? 'var(--primary)' : 'var(--border-subtle)'}`,
        backgroundColor: dragOver ? 'var(--primary-subtle)' : 'var(--bg-card)',
        borderRadius: 'var(--radius-lg)',
        padding: '40px 24px',
        textAlign: 'center',
        cursor: 'pointer',
        transition: 'all var(--transition-normal)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '12px'
      }}
    >
      <input
        type="file"
        ref={fileInputRef}
        onChange={(e) => handleFiles(e.target.files)}
        multiple
        accept=".pdf,.docx,.xlsx,.png,.jpg,.json"
        style={{ display: 'none' }}
      />
      {isUploading ? (
        <>
          <Spinner size={36} />
          <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Uploading & Processing Documents...</p>
          <p style={{ fontSize: '0.8125rem' }}>Extracting text, running OCR, building chunk vectors</p>
        </>
      ) : (
        <>
          <div style={{
            width: '52px',
            height: '52px',
            borderRadius: 'var(--radius-full)',
            backgroundColor: 'var(--primary-subtle)',
            color: 'var(--primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <UploadCloud size={26} />
          </div>
          <div>
            <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Drag and drop audit files here, or <span style={{ color: 'var(--primary)', textDecoration: 'underline' }}>browse</span>
            </p>
            <p style={{ fontSize: '0.8125rem', marginTop: '4px', color: 'var(--text-muted)' }}>
              Supports PDF, DOCX, XLSX, Images (OCR auto-enabled) up to 50MB
            </p>
          </div>
        </>
      )}
    </div>
  );
};

export default FileDropzone;
