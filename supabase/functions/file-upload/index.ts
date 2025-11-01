// File Upload Handler with Supabase Storage Integration
// Handles file uploads, validation, and storage management

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Max-Age': '86400',
};

interface UploadRequest {
  filename: string;
  fileData: string; // base64 encoded
  fileType: string;
  fileSize: number;
  userId?: string;
}

Deno.serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
    const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

    const { filename, fileData, fileType, fileSize, userId } = await req.json() as UploadRequest;

    // Validate file size (10MB limit)
    if (fileSize > 10485760) {
      throw new Error('File size exceeds 10MB limit');
    }

    // Validate file type
    const allowedTypes = ['application/pdf', 'text/csv', 'text/plain', 'application/json'];
    if (!allowedTypes.includes(fileType)) {
      throw new Error('File type not supported');
    }

    // Convert base64 to blob
    const base64Data = fileData.split(',')[1] || fileData;
    const binaryData = Uint8Array.from(atob(base64Data), c => c.charCodeAt(0));

    // Generate unique filename
    const timestamp = Date.now();
    const sanitizedFilename = filename.replace(/[^a-zA-Z0-9.-]/g, '_');
    const storagePath = `${timestamp}-${sanitizedFilename}`;

    // Upload to Supabase Storage
    const uploadResponse = await fetch(
      `${SUPABASE_URL}/storage/v1/object/uploaded-files/${storagePath}`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
          'Content-Type': fileType,
        },
        body: binaryData,
      }
    );

    if (!uploadResponse.ok) {
      const error = await uploadResponse.text();
      throw new Error(`Storage upload failed: ${error}`);
    }

    // Get public URL
    const storageUrl = `${SUPABASE_URL}/storage/v1/object/public/uploaded-files/${storagePath}`;

    // Insert file record into database
    const dbResponse = await fetch(`${SUPABASE_URL}/rest/v1/file_uploads`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
      },
      body: JSON.stringify({
        filename: storagePath,
        original_filename: filename,
        file_path: storagePath,
        file_size: fileSize,
        file_type: fileType,
        storage_bucket: 'uploaded-files',
        storage_url: storageUrl,
        uploaded_by: userId,
        upload_status: 'uploaded',
        processing_status: 'pending',
        metadata: {
          original_name: filename,
          uploaded_at: new Date().toISOString(),
        },
      }),
    });

    if (!dbResponse.ok) {
      const error = await dbResponse.text();
      throw new Error(`Database insert failed: ${error}`);
    }

    const fileRecord = await dbResponse.json();

    return new Response(
      JSON.stringify({
        success: true,
        data: {
          fileId: fileRecord[0].id,
          filename: storagePath,
          storageUrl,
          fileType,
          fileSize,
          uploadStatus: 'uploaded',
          processingStatus: 'pending',
        },
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  } catch (error) {
    console.error('File upload error:', error);
    return new Response(
      JSON.stringify({
        success: false,
        error: {
          code: 'UPLOAD_FAILED',
          message: error.message || 'File upload failed',
        },
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});
