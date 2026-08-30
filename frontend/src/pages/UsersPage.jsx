import React, { useState, useEffect } from 'react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Spinner from '../components/common/Spinner';
import { listUsers, createUser } from '../api/users';
import { UserPlus, Mail, Shield } from 'lucide-react';

const AVAILABLE_ROLES = ['admin', 'auditor', 'viewer'];

export const UsersPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);
  const [form, setForm] = useState({
    email: '',
    password: '',
    full_name: '',
    role_names: [],
  });

  const loadUsers = () => {
    setLoading(true);
    listUsers()
      .then((data) => {
        setUsers(data);
        setError(null);
      })
      .catch((err) => {
        console.error('Error fetching users:', err);
        setError(err.response?.data?.detail || 'Failed to load users.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const toggleRole = (role) => {
    setForm((f) => ({
      ...f,
      role_names: f.role_names.includes(role)
        ? f.role_names.filter((r) => r !== role)
        : [...f.role_names, role],
    }));
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      await createUser(form);
      setForm({ email: '', password: '', full_name: '', role_names: [] });
      setShowForm(false);
      loadUsers();
    } catch (err) {
      console.error('Error creating user:', err);
      setFormError(err.response?.data?.detail || 'Failed to create user.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '80px', textAlign: 'center' }}>
        <Spinner size={36} />
        <p style={{ marginTop: '16px', fontSize: '0.875rem' }}>Loading users...</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{
        padding: '24px',
        borderRadius: 'var(--radius-lg)',
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.15))',
        border: '1px solid rgba(59, 130, 246, 0.2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '4px' }}>User Management</h2>
          <p style={{ fontSize: '0.875rem' }}>Create and review platform users and their assigned roles.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm((s) => !s)}>
          <UserPlus size={16} />
          <span>{showForm ? 'Cancel' : 'New User'}</span>
        </button>
      </div>

      {error && (
        <Card>
          <p style={{ color: 'var(--accent-rose)', fontSize: '0.875rem' }}>{error}</p>
        </Card>
      )}

      {showForm && (
        <Card title="Create User">
          <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '8px' }}>
            <div style={{ display: 'flex', gap: '16px' }}>
              <input
                type="text"
                placeholder="Full name"
                required
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                style={{ flex: 1, padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}
              />
              <input
                type="email"
                placeholder="Email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                style={{ flex: 1, padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}
              />
            </div>
            <input
              type="password"
              placeholder="Temporary password"
              required
              minLength={8}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              style={{ padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}
            />
            <div>
              <div style={{ fontSize: '0.8125rem', fontWeight: 600, marginBottom: '8px' }}>Roles</div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {AVAILABLE_ROLES.map((role) => (
                  <button
                    type="button"
                    key={role}
                    onClick={() => toggleRole(role)}
                    className="btn btn-secondary"
                    style={{
                      opacity: form.role_names.includes(role) ? 1 : 0.5,
                      border: form.role_names.includes(role) ? '1px solid var(--primary)' : undefined,
                    }}
                  >
                    {role}
                  </button>
                ))}
              </div>
            </div>
            {formError && <p style={{ color: 'var(--accent-rose)', fontSize: '0.8125rem' }}>{formError}</p>}
            <button type="submit" className="btn btn-primary" disabled={submitting} style={{ alignSelf: 'flex-start' }}>
              {submitting ? 'Creating...' : 'Create User'}
            </button>
          </form>
        </Card>
      )}

      <Card title="All Users" subtitle={`${users.length} total`}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '12px' }}>
          {users.length === 0 ? (
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>No users found.</p>
          ) : (
            users.map((u) => (
              <div key={u.id} style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 12px',
                backgroundColor: 'var(--bg-surface)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Mail size={14} style={{ color: 'var(--primary)' }} />
                  <div>
                    <div style={{ fontSize: '0.8125rem', fontWeight: 600 }}>{u.full_name}</div>
                    <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>{u.email}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {u.roles.map((r) => (
                    <Badge key={r} variant="default">
                      <Shield size={10} style={{ marginRight: '4px' }} />
                      {r}
                    </Badge>
                  ))}
                  <Badge variant={u.is_active ? 'success' : 'warning'}>
                    {u.is_active ? 'active' : 'inactive'}
                  </Badge>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
};

export default UsersPage;
