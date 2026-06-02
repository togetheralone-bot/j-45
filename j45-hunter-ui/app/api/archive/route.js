import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY  // service key for writes
)

export async function POST(request) {
  const { id, archived } = await request.json()

  if (!id) {
    return Response.json({ error: 'Missing id' }, { status: 400 })
  }

  const { error } = await supabase
    .from('listings')
    .update({
      archived,
      archived_at: archived ? new Date().toISOString() : null,
    })
    .eq('id', id)

  if (error) {
    return Response.json({ error: error.message }, { status: 500 })
  }

  return Response.json({ ok: true })
}
