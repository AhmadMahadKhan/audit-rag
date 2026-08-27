import React, { useState, useEffect } from 'react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Spinner from '../components/common/Spinner';
import Toast from '../components/common/Toast';
import DocumentViewerModal from '../components/documents/DocumentViewerModal';
import { 
  performSearch, 
  getSearchSuggestions, 
  getSearchHistory, 
  listSavedSearches, 
  saveSearchQuery,
  runSavedSearch,
  deleteSavedSearch 
} from '../api/search';
import { Search, Bookmark, History, Sparkles, Filter, FileText, ArrowRight, Trash2, Eye } from 'lucide-react';

export const SearchPage = () => {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('hybrid');
  const [topK, setTopK] = useState(20);
  const [results, setResults] = useState([]);
  const [history, setHistory] = useState([]);
  const [savedSearches, setSavedSearches] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [isViewerOpen, setIsViewerOpen] = useState(false);

  const addToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  };

  useEffect(() => {
    getSearchHistory().then(setHistory).catch(() => setHistory([]));
    listSavedSearches().then(setSavedSearches).catch(() => setSavedSearches([]));
  }, []);

  // Accepts optional query override to avoid stale closure on history/saved clicks
  const handleSearch = async (e, overrideQuery) => {
    if (e) e.preventDefault();
    const q = overrideQuery !== undefined ? overrideQuery : query;
    if (!q.trim()) return;

    setLoading(true);
    try {
      const res = await performSearch(q, mode, {}, topK);
      setResults(res);
      getSearchHistory().then(setHistory).catch(() => {});
    } catch (err) {
      addToast(err.response?.data?.detail || 'Search query execution failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveCurrentSearch = async () => {
    if (!query.trim()) return;
    const name = window.prompt('Name this saved search:', query);
    if (!name) return;
    try {
      await saveSearchQuery(name, query, {}, mode);
      addToast('Saved search bookmarked!', 'success');
      const updated = await listSavedSearches();
      setSavedSearches(updated);
    } catch (err) {
      addToast('Failed to save search.', 'error');
    }
  };

  const handleRunSaved = async (searchId) => {
    setLoading(true);
    try {
      const res = await runSavedSearch(searchId);
      setResults(res);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Error running saved search.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSaved = async (searchId) => {
    try {
      await deleteSavedSearch(searchId);
      setSavedSearches((prev) => prev.filter((s) => s.id !== searchId));
      addToast('Bookmark removed', 'info');
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Search Header Bar */}
      <Card style={{ padding: '24px' }}>
        <form onSubmit={handleSearch}>
          <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search size={20} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--primary)' }} />
              <input
                type="text"
                className="form-input"
                style={{ paddingLeft: '44px', fontSize: '1rem', height: '48px' }}
                placeholder="Search across indexed audit documents, policies, tax filings, or SOC2 evidence..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ padding: '0 24px', fontSize: '0.9375rem' }} disabled={loading}>
              {loading ? <Spinner size={18} /> : (
                <>
                  <Sparkles size={16} />
                  <span>Execute RAG Search</span>
                </>
              )}
            </button>
          </div>

          {/* Mode & Filters selector */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', fontWeight: 500 }}>Vector Mode:</span>
              {['hybrid', 'semantic', 'keyword', 'entity'].map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMode(m)}
                  className={`btn ${mode === m ? 'btn-primary' : 'btn-secondary'}`}
                  style={{
                    padding: '4px 12px',
                    fontSize: '0.75rem',
                    borderRadius: 'var(--radius-full)',
                    backgroundColor: mode === m ? 'var(--primary)' : 'var(--bg-surface)'
                  }}
                >
                  {m.toUpperCase()}
                </button>
              ))}
            </div>

            {query && (
              <button type="button" className="btn btn-secondary" onClick={handleSaveCurrentSearch} style={{ fontSize: '0.8125rem', padding: '6px 12px' }}>
                <Bookmark size={14} style={{ color: 'var(--accent-amber)' }} />
                <span>Bookmark Query</span>
              </button>
            )}
          </div>
        </form>
      </Card>

      {/* Main Grid: Left Saved Searches & History, Right Search Results */}
      <div className="grid-3" style={{ gridTemplateColumns: '320px 1fr' }}>
        {/* Left Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Saved Searches */}
          <Card title="Saved Searches" subtitle="Quick access audit filters">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '10px' }}>
              {savedSearches.length > 0 ? (
                savedSearches.map((saved) => (
                  <div
                    key={saved.id}
                    style={{
                      padding: '10px 12px',
                      backgroundColor: 'var(--bg-surface)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div 
                      onClick={() => handleRunSaved(saved.id)} 
                      style={{ cursor: 'pointer', flex: 1, minWidth: 0 }}
                    >
                      <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {saved.name}
                      </div>
                      <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>{saved.search_mode} mode</div>
                    </div>
                    <button className="btn-icon" onClick={() => handleDeleteSaved(saved.id)} style={{ color: 'var(--accent-rose)', padding: '4px' }}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))
              ) : (
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>No saved searches yet.</p>
              )}
            </div>
          </Card>

          {/* Recent History */}
          <Card title="Recent History" subtitle="Audit search query log">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '10px' }}>
              {history.length > 0 ? history.map((item) => (
                <div
                  key={item.id}
                  onClick={() => { setQuery(item.query); handleSearch(null, item.query); }}
                  style={{
                    padding: '8px 10px',
                    backgroundColor: 'var(--bg-surface)',
                    borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer',
                    fontSize: '0.8125rem',
                    color: 'var(--text-secondary)'
                  }}
                >
                  <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{item.query}</div>
                  <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>{item.result_count} hits</div>
                </div>
              )) : (
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>No recent queries.</p>
              )}
            </div>
          </Card>
        </div>

        {/* Right Column: Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h3 style={{ fontSize: '1.1rem' }}>
              Search Results {results.length > 0 && <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>({results.length} vector hits)</span>}
            </h3>
          </div>

          {loading ? (
            <div style={{ padding: '60px', textAlign: 'center' }}>
              <Spinner size={32} />
              <p style={{ marginTop: '12px', fontSize: '0.875rem' }}>Reranking vector store embeddings...</p>
            </div>
          ) : results.length > 0 ? (
            results.map((res, idx) => (
              <Card key={idx}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div 
                    style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
                    onClick={() => res.document_id && (setSelectedDocId(res.document_id), setIsViewerOpen(true))}
                  >
                    <FileText size={18} style={{ color: 'var(--primary)' }} />
                    <span style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>
                      {res.document_title || res.document_id}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {res.final_score && (
                      <Badge variant="success">
                        {(res.final_score * 100).toFixed(1)}% Match
                      </Badge>
                    )}
                    <button 
                      className="btn btn-secondary" 
                      onClick={() => res.document_id && (setSelectedDocId(res.document_id), setIsViewerOpen(true))}
                      style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                    >
                      <Eye size={12} />
                      <span>Inspect</span>
                    </button>
                  </div>
                </div>

                <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--text-secondary)', marginBottom: '12px', backgroundColor: 'var(--bg-surface)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                  {res.snippet}
                </p>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <span>Section: {res.section_name || 'General'} • Page {res.page || 1}</span>
                  <span style={{ fontFamily: 'var(--font-mono)' }}>Chunk: {res.chunk_id}</span>
                </div>
              </Card>
            ))
          ) : (
            <Card style={{ padding: '48px', textAlign: 'center' }}>
              <Search size={36} style={{ color: 'var(--text-muted)', margin: '0 auto 12px' }} />
              <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Ready to perform vector search</p>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Type a query above to retrieve cited evidence from your knowledge base.
              </p>
            </Card>
          )}
        </div>
      </div>

      <DocumentViewerModal
        documentId={selectedDocId}
        isOpen={isViewerOpen}
        onClose={() => setIsViewerOpen(false)}
      />

      <Toast toasts={toasts} onDismiss={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))} />
    </div>
  );
};

export default SearchPage;
