import React, { useState, useEffect, useRef } from 'react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Spinner from '../components/common/Spinner';
import Toast from '../components/common/Toast';
import { 
  listConversations, 
  createConversation, 
  getConversationMessages, 
  sendMessage, 
  deleteConversation 
} from '../api/chat';
import { 
  MessageSquare, 
  Plus, 
  Send, 
  Trash2, 
  Bot, 
  User, 
  FileText, 
  RefreshCw, 
  Sparkles,
  ChevronRight
} from 'lucide-react';

export const ChatPage = () => {
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputQuestion, setInputQuestion] = useState('');
  const [provider, setProvider] = useState('ollama');
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [toasts, setToasts] = useState([]);
  const messagesEndRef = useRef(null);

  const addToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  };

  useEffect(() => {
    listConversations()
      .then((data) => {
        setConversations(data);
        if (data.length > 0) {
          setActiveConvId(data[0].id);
        }
      })
      .catch(() => {
        addToast('Failed to load conversations', 'error');
      });
  }, []);

  useEffect(() => {
    if (activeConvId) {
      setLoadingMessages(true);
      getConversationMessages(activeConvId)
        .then((data) => {
          setMessages(data);
          setLoadingMessages(false);
        })
        .catch((err) => {
          console.error(err);
          setLoadingMessages(false);
        });
    }
  }, [activeConvId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleCreateConv = async () => {
    try {
      const newConv = await createConversation('New Audit Analysis');
      setConversations((prev) => [newConv, ...prev]);
      setActiveConvId(newConv.id);
      setMessages([]);
    } catch (err) {
      addToast('Failed to create conversation', 'error');
    }
  };

  const handleDeleteConv = async (convId, e) => {
    e.stopPropagation();
    try {
      await deleteConversation(convId);
      const remaining = conversations.filter((c) => c.id !== convId);
      setConversations(remaining);
      if (activeConvId === convId) {
        setActiveConvId(remaining.length > 0 ? remaining[0].id : null);
      }
      addToast('Conversation deleted', 'info');
    } catch (err) {
      addToast('Failed to delete conversation', 'error');
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputQuestion.trim() || !activeConvId || sending) return;

    const userQ = inputQuestion;
    setInputQuestion('');

    const tempUserMsg = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: userQ,
      citations: [],
      created_at: new Date().toISOString()
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setSending(true);

    try {
      const res = await sendMessage(activeConvId, userQ, null, provider);
      setMessages((prev) => [...prev, res]);
    } catch (err) {
      addToast('Error receiving assistant response', 'error');
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '20px', height: 'calc(100vh - 120px)' }}>
      {/* Left Sidebar: Conversations */}
      <Card style={{ display: 'flex', flexDirection: 'column', padding: '16px' }}>
        <button 
          className="btn btn-primary" 
          onClick={handleCreateConv} 
          style={{ width: '100%', marginBottom: '16px', justifyContent: 'center' }}
        >
          <Plus size={16} />
          <span>New Audit Session</span>
        </button>

        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.05em' }}>
          Conversations
        </div>

        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {conversations.map((conv) => {
            const isActive = conv.id === activeConvId;
            return (
              <div
                key={conv.id}
                onClick={() => setActiveConvId(conv.id)}
                style={{
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: isActive ? 'var(--primary-subtle)' : 'var(--bg-surface)',
                  border: `1px solid ${isActive ? 'var(--primary)' : 'transparent'}`,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all var(--transition-fast)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                  <MessageSquare size={16} style={{ color: isActive ? 'var(--primary)' : 'var(--text-muted)', flexShrink: 0 }} />
                  <span style={{ fontSize: '0.8125rem', fontWeight: isActive ? 600 : 500, color: isActive ? 'var(--primary)' : 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {conv.title}
                  </span>
                </div>
                <button 
                  className="btn-icon" 
                  onClick={(e) => handleDeleteConv(conv.id, e)}
                  style={{ padding: '2px', color: 'var(--text-muted)' }}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Right Area: Chat Interface */}
      <Card style={{ display: 'flex', flexDirection: 'column', padding: '0', overflow: 'hidden' }}>
        {/* Header Bar */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: 'var(--bg-glass)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Bot size={20} style={{ color: 'var(--primary)' }} />
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>RAG Compliance Assistant</h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Grounded on Knowledge Base Vector Embeddings</span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>LLM Provider:</span>
            <select
              className="form-select"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              style={{ width: 'auto', padding: '4px 8px', fontSize: '0.8125rem' }}
            >
              <option value="ollama">Ollama (Cloud)</option>
            </select>
          </div>
        </div>

        {/* Message Feed */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {loadingMessages ? (
            <div style={{ padding: '40px', textAlign: 'center' }}>
              <Spinner size={28} />
            </div>
          ) : messages.length > 0 ? (
            messages.map((msg) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={msg.id}
                  style={{
                    display: 'flex',
                    gap: '12px',
                    justifyContent: isUser ? 'flex-end' : 'flex-start'
                  }}
                >
                  {!isUser && (
                    <div style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: 'var(--radius-full)',
                      backgroundColor: 'var(--primary-subtle)',
                      color: 'var(--primary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}>
                      <Bot size={18} />
                    </div>
                  )}

                  <div style={{
                    maxWidth: '75%',
                    backgroundColor: isUser ? 'var(--primary)' : 'var(--bg-surface)',
                    color: isUser ? 'white' : 'var(--text-primary)',
                    borderRadius: 'var(--radius-md)',
                    padding: '14px 18px',
                    border: isUser ? 'none' : '1px solid var(--border-subtle)',
                    boxShadow: 'var(--shadow-sm)'
                  }}>
                    <div style={{ fontSize: '0.875rem', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </div>

                    {/* Citations section */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--primary)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <FileText size={12} />
                          <span>Cited Grounding Evidence ({msg.citations.length})</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          {msg.citations.map((cit, cIdx) => (
                            <div key={cIdx} style={{ fontSize: '0.75rem', padding: '4px 8px', backgroundColor: 'var(--bg-card)', borderRadius: '4px', display: 'flex', justifyContent: 'space-between' }}>
                              <span>{cit.document_title || cit.document_id}</span>
                              <span style={{ color: 'var(--text-muted)' }}>Page {cit.page}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {isUser && (
                    <div style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: 'var(--radius-full)',
                      backgroundColor: 'var(--bg-surface)',
                      color: 'var(--text-secondary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}>
                      <User size={18} />
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
              <Sparkles size={36} style={{ margin: '0 auto 12px', color: 'var(--primary)' }} />
              <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Start an Audit Chat Conversation</p>
              <p style={{ fontSize: '0.8125rem', marginTop: '4px' }}>Ask questions about tax policies, financial statements, SOC2 guidelines, or rule findings.</p>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar Footer */}
        <form onSubmit={handleSend} style={{ padding: '16px', borderTop: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-surface)' }}>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input
              type="text"
              className="form-input"
              style={{ fontSize: '0.875rem' }}
              placeholder="Ask the Audit Assistant a question..."
              value={inputQuestion}
              onChange={(e) => setInputQuestion(e.target.value)}
              disabled={sending || !activeConvId}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={sending || !inputQuestion.trim() || !activeConvId}
              style={{ padding: '0 20px' }}
            >
              {sending ? <Spinner size={16} /> : <Send size={16} />}
            </button>
          </div>
        </form>
      </Card>

      <Toast toasts={toasts} onDismiss={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))} />
    </div>
  );
};

export default ChatPage;
