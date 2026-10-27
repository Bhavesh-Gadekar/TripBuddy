"""Create all core tables

Revision ID: 0002_data_layer
Revises: 0001_initial
Create Date: 2026-10-27 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '0002_data_layer'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('verified_id_number', sa.String(length=100), nullable=False),
        sa.Column('is_host', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('avatar', sa.String(length=500), nullable=True),
        sa.Column('superhost', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('joined_date', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # listings
    op.create_table(
        'listings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('host_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('price_per_night', sa.Integer(), nullable=False),
        sa.Column('max_guests', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('amenities', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('images', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['host_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_listings_city_price', 'listings', ['city', 'price_per_night'], unique=False)
    op.create_index(op.f('ix_listings_host_id'), 'listings', ['host_id'], unique=False)

    # reviews
    op.create_table(
        'reviews',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('listing_id', sa.String(), nullable=False),
        sa.Column('author_name', sa.String(length=100), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reviews_listing_id', 'reviews', ['listing_id'], unique=False)

    # bookings
    op.create_table(
        'bookings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('reference', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('listing_id', sa.String(), nullable=False),
        sa.Column('checkin', sa.String(length=10), nullable=False),
        sa.Column('checkout', sa.String(length=10), nullable=False),
        sa.Column('guests', sa.Integer(), nullable=False),
        sa.Column('total_price', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reference')
    )
    op.create_index('idx_bookings_listing_dates', 'bookings', ['listing_id', 'checkin', 'checkout'], unique=False)
    op.create_index(op.f('ix_bookings_reference'), 'bookings', ['reference'], unique=True)
    op.create_index(op.f('ix_bookings_user_id'), 'bookings', ['user_id'], unique=False)

    # messages
    op.create_table(
        'messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('booking_id', sa.String(), nullable=True),
        sa.Column('sender', sa.String(length=255), nullable=False),
        sa.Column('recipient', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_booking_id'), 'messages', ['booking_id'], unique=False)

    # concierge_sessions
    op.create_table(
        'concierge_sessions',
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('user_prompt', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('final_reply', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('session_id')
    )
    op.create_index(op.f('ix_concierge_sessions_user_id'), 'concierge_sessions', ['user_id'], unique=False)

    # concierge_tool_calls
    op.create_table(
        'concierge_tool_calls',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('arguments', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['concierge_sessions.session_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_concierge_tool_calls_session', 'concierge_tool_calls', ['session_id'], unique=False)


def downgrade() -> None:
    op.drop_table('concierge_tool_calls')
    op.drop_table('concierge_sessions')
    op.drop_table('messages')
    op.drop_table('bookings')
    op.drop_table('reviews')
    op.drop_table('listings')
    op.drop_table('users')

