# Note: This is a community created library and is not officially supported by the CosmosDB team.
# CosmosDB API
## Getting started
To get started and use this API, you first have to create a CosmosDB account in the Azure portal. Once this is done, just copy this example to get started:

```js
// Your AccountName, this is part of your endpoint 
// (Example: https://my-cosmosdb-account.documents.azure.com" gives "my-cosmosdb-account" as AccountName)
const accountName = "my-cosmosdb-account";

// Find this in the Azure Portal under Keys for your CosmosDB Resource
const primaryKey = '<yourPrimaryKey>'; 

// Initialize the library and connection
const API = require('./CosmosDB')(accountName, primaryKey);

// An example API call
let database = await API.database.createIfNotExists(databaseName);
```

For more calls, see below or on: https://docs.microsoft.com/en-us/rest/api/documentdb/

## Resources
### Database
#### api.database.get(dbName)
##### NodeJS Call
`await api.database.get(<dbName>)`

##### Response
```js
{ id: 'testDB',
  _rid: 'ogYeAA==',
  _self: 'dbs/ogYeAA==/',
  _etag: '"00004e00-0000-0000-0000-5ab64e0b0000"',
  _colls: 'colls/',
  _users: 'users/',
  _ts: 1521896971 }
```

#### api.database.create(dbName)
##### NodeJS Call
`await api.database.create(<dbName>)`

##### Response
```js
{ id: 'testDB',
  _rid: 'ogYeAA==',
  _self: 'dbs/ogYeAA==/',
  _etag: '"00004e00-0000-0000-0000-5ab64e0b0000"',
  _colls: 'colls/',
  _users: 'users/',
  _ts: 1521896971 }
```

#### api.database.list()
##### NodeJS Call
`await api.database.list()`

##### Response
```js
{ _rid: '',
  Databases: 
   [ { id: 'testDB',
       _rid: 'ogYeAA==',
       _self: 'dbs/ogYeAA==/',
       _etag: '"00004e00-0000-0000-0000-5ab64e0b0000"',
       _colls: 'colls/',
       _users: 'users/',
       _ts: 1521896971 } ],
  _count: 1 }
```

#### api.database.createIfNotExists(dbName)
##### NodeJS Call
`await api.database.createIfNotExists(<dbName>)`

##### Response
```js
{ id: 'testDB',
  _rid: 'ogYeAA==',
  _self: 'dbs/ogYeAA==/',
  _etag: '"00004e00-0000-0000-0000-5ab64e0b0000"',
  _colls: 'colls/',
  _users: 'users/',
  _ts: 1521896971 }
```

#### api.database.delete(dbName)
##### NodeJS Call
`await api.database.delete(<dbName>)`

##### Response
No response will be returned if successful, only an error will be thrown if problems arise.

### Collection
#### api.collection.get(dbName, collectionName)
##### NodeJS Call
`await api.collection.get(<dbName>, <collectionName>)`

##### Response
```js
{ id: 'testColl',
  indexingPolicy: 
   { indexingMode: 'consistent',
     automatic: true,
     includedPaths: [ [Object] ],
     excludedPaths: [] },
  _rid: 'ogYeAMaxxwE=',
  _ts: 1521896971,
  _self: 'dbs/ogYeAA==/colls/ogYeAMaxxwE=/',
  _etag: '"00004f00-0000-0000-0000-5ab64e0b0000"',
  _docs: 'docs/',
  _sprocs: 'sprocs/',
  _triggers: 'triggers/',
  _udfs: 'udfs/',
  _conflicts: 'conflicts/' }
```

#### api.collection.create(dbName, collectionName)
##### NodeJS Call
`await api.collection.create(<dbName>, <collectionName>)`

##### Response
```js
{ id: 'testColl',
  indexingPolicy: 
   { indexingMode: 'consistent',
     automatic: true,
     includedPaths: [ [Object] ],
     excludedPaths: [] },
  _rid: 'ogYeAMaxxwE=',
  _ts: 1521896971,
  _self: 'dbs/ogYeAA==/colls/ogYeAMaxxwE=/',
  _etag: '"00004f00-0000-0000-0000-5ab64e0b0000"',
  _docs: 'docs/',
  _sprocs: 'sprocs/',
  _triggers: 'triggers/',
  _udfs: 'udfs/',
  _conflicts: 'conflicts/' }
```

#### api.collection.list(dbName)
##### NodeJS Call
`await api.collection.list(<dbName>)`

##### Response
```js
{ _rid: 'ogYeAA==',
  DocumentCollections: 
   [ { id: 'testColl',
       indexingPolicy: [Object],
       _rid: 'ogYeAMaxxwE=',
       _ts: 1521896971,
       _self: 'dbs/ogYeAA==/colls/ogYeAMaxxwE=/',
       _etag: '"00004f00-0000-0000-0000-5ab64e0b0000"',
       _docs: 'docs/',
       _sprocs: 'sprocs/',
       _triggers: 'triggers/',
       _udfs: 'udfs/',
       _conflicts: 'conflicts/' } ],
  _count: 1 }
```

#### api.collection.createIfNotExists(dbName, collectionName)
##### NodeJS Call
`await api.collection.createIfNotExists(<dbName>, <collectionName>)`

##### Response
```js
{ id: 'testColl',
  indexingPolicy: 
   { indexingMode: 'consistent',
     automatic: true,
     includedPaths: [ [Object] ],
     excludedPaths: [] },
  _rid: 'ogYeAMaxxwE=',
  _ts: 1521896971,
  _self: 'dbs/ogYeAA==/colls/ogYeAMaxxwE=/',
  _etag: '"00004f00-0000-0000-0000-5ab64e0b0000"',
  _docs: 'docs/',
  _sprocs: 'sprocs/',
  _triggers: 'triggers/',
  _udfs: 'udfs/',
  _conflicts: 'conflicts/' }
```

#### api.collection.delete(dbName, collectionName)
##### NodeJS Call
`await api.collection.delete(<dbName>, <collectionName>)`

##### Response
No response will be returned if successful, only an error will be thrown if problems arise.

#### api.collection.truncate(dbName, collectionName)
Truncates the collection.

> Note: This will delete and recreate the collection, so the ID will change

##### NodeJS Call
`await api.collection.truncate(<dbName>, <collectionName>)`

##### Response
No response will be returned if successful, only an error will be thrown if problems arise.


### Document
#### api.document.get(dbName, collectionName, documentId)
##### NodeJS Call
`await api.document.get(<dbName>, <collectionName>, <documentId>)`

##### Response
```js
{ id: 'test-doc',
  hello: 'world',
  obj: { test: 'doc' },
  arr: [ 'el1', 'el2' ],
  _rid: 'ogYeAMaxxwEBAAAAAAAAAA==',
  _self: 'dbs/ogYeAA==/colls/ogYeAMaxxwE=/docs/ogYeAMaxxwEBAAAAAAAAAA==/',
  _etag: '"00006a59-0000-0000-0000-5ab64e0c0000"',
  _attachments: 'attachments/',
  _ts: 1521896972 }
```

#### api.document.create(dbName, collectionName, document)
##### NodeJS Call
`await api.document.create(<dbName>, <collectionName>, <document>)`

###### Example
```js
const newDoc = await api.document.create('testDB', 'testColl', {
  id: 'test-doc',
  hello: 'world',
  obj: {
      test: 'doc'
  },
  arr: [ "el1", "el2" ]
})
```

##### Response
```js
{ id: 'test-doc',
  hello: 'world',
  obj: { test: 'doc' },
  arr: [ 'el1', 'el2' ],
  _rid: 'ogYeAMaxxwEBAAAAAAAAAA==',
  _self: 'dbs/ogYeAA==/colls/ogYeAMaxxwE=/docs/ogYeAMaxxwEBAAAAAAAAAA==/',
  _etag: '"00006a59-0000-0000-0000-5ab64e0c0000"',
  _attachments: 'attachments/',
  _ts: 1521896972 }
```

#### api.document.list(dbName, collectionName)
##### NodeJS Call
`await api.document.list(<dbName>, <collectionName>)`

##### Response
```js
{ _rid: 'ogYeAMaxxwE=',
  Documents: 
   [ { id: 'test-doc',
       hello: 'world',
       obj: [Object],
       arr: [Array],
       _rid: 'ogYeAMaxxwEBAAAAAAAAAA==',
       _self: 'dbs/ogYeAA==/colls/ogYeAMaxxwE=/docs/ogYeAMaxxwEBAAAAAAAAAA==/',
       _etag: '"00006a59-0000-0000-0000-5ab64e0c0000"',
       _attachments: 'attachments/',
       _ts: 1521896972 } ],
  _count: 1 }
```

#### api.document.query(dbName, collectionName, <query>)
##### NodeJS Call
`await api.document.query(<dbName>, <collectionName>, <query>)`

###### Example
```js
const myDoc = await api.document.query('testDB', 'testColl', {
  query: `SELECT * FROM ${collectionName} c WHERE c.id = @id`,
  parameters: [
    {
      name: '@id',
      value: doc.id
    }
  ]
})
```

##### Response
```js
{ _rid: 'oQVCAKobrAE=',
  Documents:
   [ { id: 'test-doc',
       hello: 'world',
       obj: [Object],
       arr: [Array],
       _rid: 'ogYeAMaxxwEBAAAAAAAAAA==',
       _self: 'dbs/ogYeAA==/colls/ogYeAMaxxwE=/docs/ogYeAMaxxwEBAAAAAAAAAA==/',
       _etag: '"00006a59-0000-0000-0000-5ab64e0c0000"',
       _attachments: 'attachments/',
       _ts: 1521897637 } ],
  _count: 1 }
```

#### api.document.createIfNotExists(dbName, collectionName, document)
##### NodeJS Call
`await api.document.createIfNotExists(<dbName>, <collectionName>, <document>)`

###### Example
```js
const newDoc = await api.document.create('testDB', 'testColl', {
  id: 'test-doc',
  hello: 'world',
  obj: {
      test: 'doc'
  },
  arr: [ "el1", "el2" ]
})
```

##### Response
```js
{ id: 'test-doc',
  hello: 'world',
  obj: { test: 'doc' },
  arr: [ 'el1', 'el2' ],
  _rid: 'ogYeAMaxxwEBAAAAAAAAAA==',
  _self: 'dbs/ogYeAA==/colls/ogYeAMaxxwE=/docs/ogYeAMaxxwEBAAAAAAAAAA==/',
  _etag: '"00006a59-0000-0000-0000-5ab64e0c0000"',
  _attachments: 'attachments/',
  _ts: 1521896972 }
```

#### api.document.delete(dbName, collectionName, documentId)
##### NodeJS Call
`await api.document.delete(<dbName>, <collectionName>, <documentId>)`

##### Response
No response will be returned if successful, only an error will be thrown if problems arise.
