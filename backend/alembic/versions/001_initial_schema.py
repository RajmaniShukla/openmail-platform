"""Initial database schema for OpenMail

Revision ID: 001
Revises: 
Create Date: 2024-02-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types
    op.execute("CREATE TYPE user_role AS ENUM ('user', 'admin', 'super_admin')")
    op.execute("CREATE TYPE folder_type AS ENUM ('inbox', 'sent', 'drafts', 'spam', 'trash', 'starred', 'archive', 'custom')")
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100)),
        sa.Column('last_name', sa.String(100)),
        sa.Column('display_name', sa.String(200)),
        sa.Column('role', sa.Enum('user', 'admin', 'super_admin', name='user_role'), default='user'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('timezone', sa.String(50), default='UTC'),
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('avatar_url', sa.String(500)),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Domains table
    op.create_table(
        'domains',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('mx_verified', sa.Boolean, default=False),
        sa.Column('spf_verified', sa.Boolean, default=False),
        sa.Column('dkim_verified', sa.Boolean, default=False),
        sa.Column('dmarc_verified', sa.Boolean, default=False),
        sa.Column('dkim_selector', sa.String(100), default='default'),
        sa.Column('dkim_private_key', sa.Text),
        sa.Column('dkim_public_key', sa.Text),
        sa.Column('verification_token', sa.String(100)),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('is_primary', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Mailboxes table
    op.create_table(
        'mailboxes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('domain_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('domains.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('local_part', sa.String(64), nullable=False),
        sa.Column('display_name', sa.String(200)),
        sa.Column('is_primary', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('quota_bytes', sa.BigInteger, default=5368709120),  # 5GB
        sa.Column('used_bytes', sa.BigInteger, default=0),
        sa.Column('signature_html', sa.Text),
        sa.Column('signature_text', sa.Text),
        sa.Column('auto_reply_enabled', sa.Boolean, default=False),
        sa.Column('auto_reply_subject', sa.String(500)),
        sa.Column('auto_reply_body', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('local_part', 'domain_id', name='uq_mailbox_local_domain'),
    )
    
    # Folders table
    op.create_table(
        'folders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('mailbox_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mailboxes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('type', sa.Enum('inbox', 'sent', 'drafts', 'spam', 'trash', 'starred', 'archive', 'custom', name='folder_type'), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('folders.id', ondelete='CASCADE')),
        sa.Column('color', sa.String(7)),
        sa.Column('icon', sa.String(50)),
        sa.Column('position', sa.Integer, default=0),
        sa.Column('is_system', sa.Boolean, default=False),
        sa.Column('unread_count', sa.Integer, default=0),
        sa.Column('total_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('mailbox_id', 'name', 'parent_id', name='uq_folder_mailbox_name_parent'),
    )
    
    # Labels table
    op.create_table(
        'labels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('mailbox_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mailboxes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('color', sa.String(7), default='#3B82F6'),
        sa.Column('description', sa.String(255)),
        sa.Column('is_visible', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('mailbox_id', 'name', name='uq_label_mailbox_name'),
    )
    
    # Emails table
    op.create_table(
        'emails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('mailbox_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mailboxes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('folder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('folders.id', ondelete='SET NULL'), index=True),
        sa.Column('message_id', sa.String(500), unique=True, nullable=False, index=True),
        sa.Column('thread_id', sa.String(100), index=True),
        sa.Column('in_reply_to', sa.String(500)),
        sa.Column('references', postgresql.ARRAY(sa.String(500))),
        sa.Column('from_address', sa.String(255), nullable=False, index=True),
        sa.Column('from_name', sa.String(200)),
        sa.Column('to_addresses', postgresql.ARRAY(sa.String(255)), nullable=False),
        sa.Column('cc_addresses', postgresql.ARRAY(sa.String(255)), default=[]),
        sa.Column('bcc_addresses', postgresql.ARRAY(sa.String(255)), default=[]),
        sa.Column('reply_to', sa.String(255)),
        sa.Column('subject', sa.String(1000)),
        sa.Column('body_html', sa.Text),
        sa.Column('body_text', sa.Text),
        sa.Column('snippet', sa.String(500)),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('raw_headers', postgresql.JSONB),
        sa.Column('headers', postgresql.JSONB),
        sa.Column('is_read', sa.Boolean, default=False, index=True),
        sa.Column('is_starred', sa.Boolean, default=False, index=True),
        sa.Column('is_draft', sa.Boolean, default=False),
        sa.Column('is_important', sa.Boolean, default=False),
        sa.Column('has_attachments', sa.Boolean, default=False, index=True),
        sa.Column('spam_score', sa.Float),
        sa.Column('size_bytes', sa.Integer, default=0),
        sa.Column('raw_email_path', sa.String(500)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Email-Label junction table
    op.create_table(
        'email_labels',
        sa.Column('email_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('emails.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('label_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('labels.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Attachments table
    op.create_table(
        'attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('emails.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=False),
        sa.Column('size_bytes', sa.Integer, nullable=False),
        sa.Column('content_id', sa.String(255)),
        sa.Column('is_inline', sa.Boolean, default=False),
        sa.Column('storage_path', sa.String(500), nullable=False),
        sa.Column('checksum', sa.String(64)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Email filters table
    op.create_table(
        'email_filters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('mailbox_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mailboxes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('priority', sa.Integer, default=0),
        sa.Column('conditions', postgresql.JSONB, nullable=False),
        sa.Column('actions', postgresql.JSONB, nullable=False),
        sa.Column('stop_processing', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Contacts table
    op.create_table(
        'contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('name', sa.String(200)),
        sa.Column('first_name', sa.String(100)),
        sa.Column('last_name', sa.String(100)),
        sa.Column('phone', sa.String(50)),
        sa.Column('company', sa.String(200)),
        sa.Column('avatar_url', sa.String(500)),
        sa.Column('notes', sa.Text),
        sa.Column('is_favorite', sa.Boolean, default=False),
        sa.Column('frequency', sa.Integer, default=0),  # Contact frequency
        sa.Column('last_contacted', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('user_id', 'email', name='uq_contact_user_email'),
    )
    
    # Sessions table (for refresh tokens)
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('refresh_token', sa.String(500), unique=True, nullable=False, index=True),
        sa.Column('device_info', sa.String(500)),
        sa.Column('ip_address', sa.String(50)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime(timezone=True)),
    )
    
    # Create indexes for common queries
    op.create_index('ix_emails_mailbox_folder_date', 'emails', ['mailbox_id', 'folder_id', 'date'])
    op.create_index('ix_emails_mailbox_thread', 'emails', ['mailbox_id', 'thread_id'])
    op.create_index('ix_emails_mailbox_unread', 'emails', ['mailbox_id', 'is_read'], postgresql_where=sa.text('is_read = false'))
    op.create_index('ix_folders_mailbox_type', 'folders', ['mailbox_id', 'type'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('sessions')
    op.drop_table('contacts')
    op.drop_table('email_filters')
    op.drop_table('attachments')
    op.drop_table('email_labels')
    op.drop_table('emails')
    op.drop_table('labels')
    op.drop_table('folders')
    op.drop_table('mailboxes')
    op.drop_table('domains')
    op.drop_table('users')
    
    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS folder_type')
    op.execute('DROP TYPE IF EXISTS user_role')
