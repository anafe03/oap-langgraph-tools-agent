import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://gdmdurzaeezcrgrmtabx.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdkbWR1cnphZWV6Y3Jncm10YWJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1OTk3MDUsImV4cCI6MjA2MzE3NTcwNX0.xbuXRr2jDAAG021blK5zeuqwO-5zMNq7_tEfW_oW7cQ'
)

const { data, error } = await supabase.auth.signInWithPassword({
  email: 'austinnafe@aol.com',
  password: 'password123'
})

console.log('ACCESS TOKEN:', data?.session?.access_token)
