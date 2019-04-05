import { adalApiFetch } from '../../configAdal';
import fetch from 'isomorphic-fetch';
import download from "downloadjs";
import Config from '../../config';

export const getFileSystems = async () => {
    const res = await adalApiFetch(fetch, `https://${Config.storageAccountName}.dfs.core.windows.net/?resource=account`);
    const json = await res.json();

    if (json.error) {
        throw new Error(JSON.stringify(json.error));
    }

    return json.filesystems;
}

export const getFileSystem = async (name) => {
    const res = await adalApiFetch(fetch, `https://${Config.storageAccountName}.dfs.core.windows.net/${name}?recursive=false&resource=filesystem`);
    const json = await res.json();

    if (json.error) {
        throw new Error(JSON.stringify(json.error));
    }

    return json.paths;
}

export const fileSystemDelete = async (name) => {
    console.log(name);
    const res = await adalApiFetch(fetch, `https://${Config.storageAccountName}.dfs.core.windows.net/${name}?resource=filesystem`, { method: 'DELETE' });
    
    // StatusCode 200 should be returned - 200 Success
    if (res.status != 200) {
        alert("Something happened while deleting the folder");
        return false;
    }

    return true;
}

export const getFileSystemPath = async (fileSystemName, path) => {
    const res = await adalApiFetch(fetch, ''
        + `https://${Config.storageAccountName}.dfs.core.windows.net`
        + `/${fileSystemName}`
        + `?directory=${path}&recursive=false&resource=filesystem`
    );

    const json = await res.json();

    // console.log('FOUND PATHS, CURRENT PATH: ' + this.state.path + ' SELECTED PATH: ' + path)
    // console.log(this.state);
    // console.log(json.paths);
    // console.log('END FOUND PATHS')

    // @todo: should show an error
    if (!json || !json.paths) {
        throw new Error(JSON.stringify({ code: 'Unknown', message: 'Nothing found' }));
    }

    if (json.error) {
        throw new Error(JSON.stringify(json.error));
    }

    return json.paths;
}

export const fileSystemFolderDelete = async (fileSystemName, folderPath, folderName) => {
    // Create the folder on the ADLS and reload the current path
    // https://docs.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/delete
    const res = await adalApiFetch(fetch, ''
        + `https://${Config.storageAccountName}.dfs.core.windows.net`
        + `/${fileSystemName}`
        + `${folderPath}/${folderName}?recursive=true`,
        {
            method: 'DELETE'
        }
    );

    // StatusCode 200 should be returned - 200 Success
    if (res.status != 200) {
        alert("Something happened while deleting the folder");
        return false;
    }

    return true;
}

export const fileSystemFolderCreate = async (fileSystemName, folderPath, folderName) => {
    if (!folderName || folderName == "") {
        return;
    }
    
    // Create the folder on the ADLS and reload the current path
    // PUT http://{accountName}.{dnsSuffix}/{filesystem}/{path}?resource={resource}&continuation={continuation}&mode={mode}&timeout={timeout}
    // https://docs.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/create
    const res = await adalApiFetch(fetch, ''
        + `https://${Config.storageAccountName}.dfs.core.windows.net`
        + `/${fileSystemName}`
        + `${folderPath}/${folderName}?resource=directory`,
        {
            method: 'PUT'
        }
    );

    // StatusCode 201 should be returned - 201 Created
    if (res.status != 201) {
        alert("Something happened while creating the folder");
        return false;
    }

    return true;
}

export const fileSystemFileDownload = async (fileSystemName, filePath, fileName) => {
    const res = await adalApiFetch(fetch, ''
        + `https://${Config.storageAccountName}.dfs.core.windows.net`
        + `/${fileSystemName}`
        + `${filePath}/${fileName}`
    );

    const blob = await res.blob();
    download(blob, fileName);
}

export const fileSystemFileDelete = async (fileSystemName, filePath, fileName) => {
    // https://docs.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/delete
    const res = await adalApiFetch(fetch, ''
        + `https://${Config.storageAccountName}.dfs.core.windows.net`
        + `/${fileSystemName}`
        + `${filePath}/${fileName}`,
        {
            method: 'DELETE'
        }
    );

    // StatusCode 201 should be returned - 201 Created
    if (res.status != 200) {
        alert("Something happened while deleting the folder");
        return false;
    }

    return true;
}

// https://docs.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/create -> create
// https://docs.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/update -> upload and flush
// 3 steps:
// * ?resource=file -> PUT
// * ?action=append&position=offset -> PATCH application/octet-stream
// * ?action=flush&position=offfset -> PATCH application/octet-stream
export const fileSystemFileUpload = async (fileSystemName, filePath, fileName, fileBlob, cbUploadProgress) => {
    const BYTES_PER_CHUNK = 1048576 * 1; // 5Mb

    // 1. Create File Placeholder
    const res = await adalApiFetch(fetch, ''
        + `https://${Config.storageAccountName}.dfs.core.windows.net`
        + `/${fileSystemName}`
        + `${filePath}/${fileName}?resource=file`,
        {
            method: 'PUT'
        }
    );

    // 2. Append Content
    let chunkCount = Math.max(Math.ceil(fileBlob.size / BYTES_PER_CHUNK), 1);

    console.log(`Sending ${chunkCount} chunks`);

    for (let i = 0; i < fileBlob.size; i += BYTES_PER_CHUNK) {
        console.log(`Sending ${i}/${fileBlob.size}`);
        let chunkBlob = fileBlob.slice(i, i + BYTES_PER_CHUNK);

        // Callback for progress
        cbUploadProgress(fileBlob.size, i);

        // Upload the different chinks
        console.log(chunkBlob.size);
        const resAppend = await adalApiFetch(fetch, ''
            + `https://${Config.storageAccountName}.dfs.core.windows.net`
            + `/${fileSystemName}`
            + `${filePath}/${fileName}?action=append&position=${i}`,
            {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/octet-stream',
                    'Content-Length': chunkBlob.size,
                    'X-HTTP-Method-Override': 'PATCH' // Currently send it as a PUT since PATCH is not supported
                },
                body: chunkBlob
            }
        );
    }

    // 3. Flush the file
    const resFlush = await adalApiFetch(fetch, ''
        + `https://${Config.storageAccountName}.dfs.core.windows.net`
        + `/${fileSystemName}`
        + `${filePath}/${fileName}?action=flush&position=${fileBlob.size}`,
        {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/octet-stream',
                'X-HTTP-Method-Override': 'PATCH' // Currently send it as a PUT since PATCH is not supported
            }
        }
    );

    // Callback for progress stating that we are done
    cbUploadProgress(fileBlob.size, fileBlob.size);
}