'use client'

import { useEffect, useState, useCallback } from 'react'
import { supabase } from '../lib/supabase'

const SOURCE_COLORS = {
  'Reverb':                '#e05c00',
  'eBay':                  '#0064d2',
  'GBase':                 '#2d6a2d',
  'Craigslist':            '#7b3f9e',
  'Facebook Marketplace':  '#1877f2',
  'Acoustic Guitar Forum': '#8b4513',
  'Guitar Center':         '#c8102e',
  'The Gear Page':         '#2b5797',
  'Bernunzio Uptown Music':'#8b6914',
  'Emerald City Guitars':  '#2e7d32',
  'Carter Vintage':        '#1a1a1a',
  "Norman's Rare Guitars": '#1a1a1a',
  'Austin Vintage Guitars':'#bf4300',
  'Rumble Seat Music':     '#7b3f9e',
  'Dream Guitars':         '#2e7d32',
  'Acoustic Vibes Music':  '#1b6ca8',
}

function sourceColor(source) {
  for (const [key, color] of Object.entries(SOURCE_COLORS)) {
    if (source?.includes(key)) return color
  }
  return '#555'
}

function Stars({ score }) {
  const filled = Math.min(score, 5)
  const empty  = 5 - filled
  return (
    <span style={{ letterSpacing: 1 }}>
      <span style={{ color: '#c8a84b' }}>{'★'.repeat(filled)}</span>
      <span style={{ color: '#ddd' }}>{'★'.repeat(empty)}</span>
    </span>
  )
}

function ListingCard({ listing, onArchive, compact = false }) {
  const [archiving, setArchiving] = useState(false)
  const color    = sourceColor(listing.source)
  const archived = listing.archived

  async function handleArchive() {
    setArchiving(true)
    await onArchive(listing.id, !archived)
    setArchiving(false)
  }

  return (
    <div style={{
      display: 'flex',
      gap: 14,
      padding: compact ? '12px 16px' : '16px 20px',
      background: archived ? '#f7f7f7' : '#fff',
      borderRadius: 8,
      border: archived
        ? '1px solid #e8e8e8'
        : compact
          ? '1px solid #e8e4dc'
          : '2px solid #c8a84b',
      opacity: archived ? 0.5 : 1,
      transition: 'opacity 0.2s',
      marginBottom: compact ? 8 : 12,
    }}>
      {/* Image */}
      <a href={listing.url} target="_blank" rel="noreferrer"
        style={{ flexShrink: 0 }}>
        {listing.image_url ? (
          <img
            src={listing.image_url}
            alt={listing.title}
            style={{
              width: compact ? 72 : 110,
              height: compact ? 54 : 82,
              objectFit: 'cover',
              borderRadius: 6,
              border: '1px solid #e8e4dc',
              display: 'block',
            }}
          />
        ) : (
          <div style={{
            width: compact ? 72 : 110,
            height: compact ? 54 : 82,
            background: '#f0ede8',
            borderRadius: 6,
            border: '1px solid #e8e4dc',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: compact ? 20 : 28,
          }}>🎸</div>
        )}
      </a>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <a href={listing.url} target="_blank" rel="noreferrer"
          style={{
            fontSize: compact ? 13 : 15,
            fontWeight: 600,
            color: '#1a1a1a',
            textDecoration: 'none',
            display: 'block',
            marginBottom: 5,
            lineHeight: 1.3,
          }}>
          {listing.title}
        </a>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
          <span style={{
            background: color + '18',
            color,
            border: `1px solid ${color}40`,
            borderRadius: 4,
            padding: '2px 8px',
            fontSize: 11,
            fontWeight: 600,
          }}>{listing.source}</span>
          <Stars score={listing.score} />
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {(listing.match_reasons || []).map(r => (
            <span key={r} style={{
              background: '#eef6ee',
              color: '#2d6a2d',
              borderRadius: 4,
              padding: '2px 7px',
              fontSize: 11,
              fontWeight: 500,
            }}>{r}</span>
          ))}
        </div>
      </div>

      {/* Right side */}
      <div style={{
        flexShrink: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        justifyContent: 'space-between',
        gap: 8,
        minWidth: compact ? 90 : 110,
      }}>
        <div style={{
          fontSize: compact ? 18 : 22,
          fontWeight: 700,
          color: '#1a1a1a',
          letterSpacing: -0.5,
          whiteSpace: 'nowrap',
        }}>
          {listing.price ? `$${listing.price.toLocaleString()}` : 'POA'}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-end' }}>
          <a href={listing.url} target="_blank" rel="noreferrer"
            style={{
              background: '#1a1a1a',
              color: '#fff',
              fontSize: 12,
              fontWeight: 500,
              padding: '6px 12px',
              borderRadius: 5,
              textDecoration: 'none',
              whiteSpace: 'nowrap',
            }}>
            View →
          </a>
          <button
            onClick={handleArchive}
            disabled={archiving}
            style={{
              background: 'none',
              border: `1px solid ${archived ? '#2d6a2d' : '#ccc'}`,
              color: archived ? '#2d6a2d' : '#888',
              fontSize: 11,
              padding: '4px 10px',
              borderRadius: 4,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s',
            }}>
            {archiving ? '...' : archived ? '↩ Restore' : 'Archive'}
          </button>
        </div>
      </div>
    </div>
  )
}

function Section({ title, listings, onArchive, compact = false, gold = false }) {
  if (!listings.length) return null
  return (
    <div style={{ marginBottom: 32 }}>
      <div style={{
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: '0.8px',
        textTransform: 'uppercase',
        color: gold ? '#c8a84b' : '#888',
        marginBottom: 12,
        display: 'flex',
        alignItems: 'center',
        gap: 6,
      }}>
        {gold && <span>✦</span>}
        {title} <span style={{ fontWeight: 400, opacity: 0.6 }}>({listings.length})</span>
      </div>
      {listings.map(l => (
        <ListingCard
          key={l.id}
          listing={l}
          onArchive={onArchive}
          compact={compact}
        />
      ))}
    </div>
  )
}

export default function Home() {
  const [listings, setListings]     = useState([])
  const [loading, setLoading]       = useState(true)
  const [showArchived, setShowArchived] = useState(false)
  const [lastUpdated, setLastUpdated]   = useState(null)

  async function fetchListings() {
    const { data, error } = await supabase
      .from('listings')
      .select('*')
      .order('score', { ascending: false })
      .order('price', { ascending: true })
      .limit(500)

    if (!error && data) {
      setListings(data)
      setLastUpdated(new Date())
    }
    setLoading(false)
  }

  useEffect(() => { fetchListings() }, [])

  const handleArchive = useCallback(async (id, archived) => {
    // Optimistic update
    setListings(prev => prev.map(l =>
      l.id === id ? { ...l, archived } : l
    ))

    const resp = await fetch('/api/archive', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, archived }),
    })

    if (!resp.ok) {
      // Revert on failure
      setListings(prev => prev.map(l =>
        l.id === id ? { ...l, archived: !archived } : l
      ))
    }
  }, [])

  const active   = listings.filter(l => !l.archived)
  const archived = listings.filter(l =>  l.archived)

  const newJ45   = active.filter(l =>  l.is_j45)
  const newOther = active.filter(l => !l.is_j45)
  const archJ45  = archived.filter(l =>  l.is_j45)
  const archOther= archived.filter(l => !l.is_j45)

  return (
    <div style={{
      minHeight: '100vh',
      background: '#f0ede8',
      fontFamily: "-apple-system, 'Helvetica Neue', Arial, sans-serif",
    }}>
      {/* Header */}
      <div style={{
        background: '#1a1a1a',
        padding: '20px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 24 }}>🎸</span>
          <div>
            <div style={{ color: '#fff', fontSize: 17, fontWeight: 600, letterSpacing: -0.3 }}>
              J45 Hunter
            </div>
            <div style={{ color: '#888', fontSize: 12 }}>
              1956–1965 · $2,000–$7,500 · J-45, J-50, Country Western
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {lastUpdated && (
            <span style={{ color: '#666', fontSize: 12 }}>
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchListings}
            style={{
              background: '#333',
              border: 'none',
              color: '#fff',
              padding: '7px 14px',
              borderRadius: 6,
              fontSize: 12,
              cursor: 'pointer',
            }}>
            Refresh
          </button>
        </div>
      </div>

      {/* Stats bar */}
      {!loading && (
        <div style={{
          background: '#f7f5f0',
          borderBottom: '1px solid #e8e4dc',
          padding: '12px 24px',
          display: 'flex',
          gap: 32,
        }}>
          {[
            ['Active',   active.length],
            ['J-45',     newJ45.length],
            ['J-50 / CW',newOther.length],
            ['Archived', archived.length],
          ].map(([label, count]) => (
            <div key={label}>
              <div style={{ fontSize: 18, fontWeight: 700, color: '#1a1a1a', lineHeight: 1 }}>
                {count}
              </div>
              <div style={{ fontSize: 11, color: '#888', marginTop: 2 }}>{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Body */}
      <div style={{ maxWidth: 780, margin: '0 auto', padding: '24px 16px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 60, color: '#888' }}>
            Loading listings...
          </div>
        ) : active.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 60, color: '#888' }}>
            No active listings found.
          </div>
        ) : (
          <>
            <Section title="J-45"                    listings={newJ45}    onArchive={handleArchive} gold />
            <Section title="J-50 & Country Western"  listings={newOther}  onArchive={handleArchive} gold />

            {/* Archived toggle */}
            {archived.length > 0 && (
              <>
                <button
                  onClick={() => setShowArchived(v => !v)}
                  style={{
                    background: 'none',
                    border: '1px solid #ddd',
                    borderRadius: 6,
                    padding: '8px 16px',
                    fontSize: 12,
                    color: '#888',
                    cursor: 'pointer',
                    marginBottom: 24,
                    display: 'block',
                  }}>
                  {showArchived ? '▲ Hide' : '▼ Show'} archived ({archived.length})
                </button>

                {showArchived && (
                  <>
                    <Section title="Archived — J-45"               listings={archJ45}   onArchive={handleArchive} compact />
                    <Section title="Archived — J-50 & Country Western" listings={archOther} onArchive={handleArchive} compact />
                  </>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}
