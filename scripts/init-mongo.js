// MongoDB initialization script
db = db.getSiblingDB('audio_converter');

// Create collections with validation
db.createCollection('jobs', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['id', 'filename', 'status', 'created_at'],
      properties: {
        id: { bsonType: 'string' },
        filename: { bsonType: 'string' },
        status: { enum: ['pending', 'processing', 'completed', 'failed'] },
        progress: { bsonType: 'int', minimum: 0, maximum: 100 },
        message: { bsonType: 'string' },
        output_file: { bsonType: ['string', 'null'] },
        created_at: { bsonType: 'date' },
        updated_at: { bsonType: 'date' }
      }
    }
  }
});

// Create indexes for performance
db.jobs.createIndex({ id: 1 }, { unique: true });
db.jobs.createIndex({ status: 1 });
db.jobs.createIndex({ created_at: -1 });

// Create user for application
db.createUser({
  user: 'app_user',
  pwd: 'app_password',
  roles: [
    { role: 'readWrite', db: 'audio_converter' }
  ]
});

print('MongoDB initialized successfully');
