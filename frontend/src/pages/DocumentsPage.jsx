import React, { useState, useEffect } from 'react';
import FileDropzone from '../components/documents/FileDropzone';
import DocumentViewerModal from '../components/documents/DocumentViewerModal';
import Table from '../components/common/Table';
import Badge from '../components/common/Badge';
import Card from '../components/common/Card';
import Spinner from '../components/common/Spinner';
import Toast from '../components/common/Toast';
import { listDocuments, uploadDocuments, deleteDocument } from '../api/documents';
import { FileText, Eye, Trash2, Search, Filter } from 'lucide-react';

export const DocumentsPage = () => {
  const [documents, setDocuments] = useState([]);
  const [filteredDocs, setFilteredDocs] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  const fetchDocs = () => {
    setLoading(true);
    listDocuments()
      .then((data) => {
        setDocuments(data);
        setFilteredDocs(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching documents:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  useEffect(() => {
    if (!searchQuery) {
      setFilteredDocs(documents);
    } else {
      const q = searchQuery.toLowerCase();
      setFilteredDocs(documents.filter((d) => d.original_filename.toLowerCase().includes(q) || d.status.toLowerCase().includes(q)));
    }
  }, [searchQuery, documents]);

  const handleUpload = async (files) => {
    setIsUploading(true);
    try {
      const res = await uploadDocuments(files);
      addToast(`Successfully processed ${res.success_count} documents!`, 'success');
      fetchDocs();
    } catch (err) {
      addToast('Document upload failed.', 'error');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;
    try {
      await deleteDocument(docId);
      addToast('Document deleted successfully', 'success');
      fetchDocs();
    } catch (err) {
      addToast('Failed to delete document', 'error');
    }
  };

  const handleOpenViewer = (docId) => {
    setSelectedDocId(docId);
    setIsViewerOpen(true);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const columns = [
    {
      header: 'Document Name',
      accessor: 'original_filename',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <FileText size={18} style={{ color: 'var(--primary)', flexShrink: 0 }} />
          <div>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{row.original_filename}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ID: {row.id}</div>
          </div>
        </div>
      )
    },
    {
      header: 'File Size',
      accessor: 'file_size',
      render: (row) => <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem' }}>{formatFileSize(row.file_size)}</span>
    },
    {
      header: 'Status',
      accessor: 'status',
      render: (row) => {
        const variant = row.status === 'indexed' ? 'success' : row.status === 'processing' ? 'warning' : 'danger';
        return <Badge variant={variant}>{row.status}</Badge>;
      }
    },
    {
      header: 'Ingested On',
      accessor: 'created_at',
      render: (row) => <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>{new Date(row.created_at).toLocaleDateString()}</span>
    },
    {
      header: 'Actions',
      style: { width: '120px', textAlign: 'right' },
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '6px' }}>
          <button
            className="btn-icon"
            title="Inspect Deep Bundle"
            onClick={() => handleOpenViewer(row.id)}
          >
            <Eye size={16} />
          </button>
          <button
            className="btn-icon"
            title="Delete Document"
            onClick={() => handleDelete(row.id)}
            style={{ color: 'var(--accent-rose)' }}
          >
            <Trash2 size={16} />
          </button>
        </div>
      )
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <FileDropzone onUpload={handleUpload} isUploading={isUploading} />

      <Card
        title="Ingested Knowledge Base Documents"
        subtitle="Manage uploaded financial statements, compliance audits, and tax filings"
        action={
          <div style={{ position: 'relative', width: '260px' }}>
            <Search size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: '34px', fontSize: '0.8125rem' }}
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        }
      >
        {loading ? (
          <div style={{ padding: '60px', textAlign: 'center' }}>
            <Spinner size={32} />
          </div>
        ) : (
          <Table columns={columns} data={filteredDocs} />
        )}
      </Card>

      <DocumentViewerModal
        documentId={selectedDocId}
        isOpen={isViewerOpen}
        onClose={() => setIsViewerOpen(false)}
      />

      <Toast toasts={toasts} onDismiss={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))} />
    </div>
  );
};

export default DocumentsPage;
