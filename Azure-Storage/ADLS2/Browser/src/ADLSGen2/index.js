import React, { Component } from 'react';
import fetch from 'isomorphic-fetch';
import { adalApiFetch } from '../configAdal';
import Menu from './Menu';
import MenuItem from './MenuItem';
import FileSystem from './FileSystem';
import FileSystemPath from './FileSystemResources';
import FileSystemPathResourceFile from './FileSystemPathResourceFile';
import FileSystemPathResourceFolder from './FileSystemPathResourceFolder';
import download from "downloadjs";
import * as API from './API/Gen2';
import UploadProgress from './UploadProgress';
import "./Index.css";

class ADLSGen2 extends Component {
    state = {
        fileSystems: [],
        isLoading: true
    }

    async componentDidMount() {
        await this.adlsListFileSystems();
    }

    async adlsListFileSystems() {
        this.setState({ isLoading: true });

        const fileSystems = await API.getFileSystems();

        this.setState({
            isLoading: false,
            fileSystems: fileSystems,
            selectedFileSystem: null,
            path: "",
            paths: []
        })
    }

    async onClickFileSystemDelete(fileSystemName) {
        if (!window.confirm("Are you sure you wish to delete this filesystem?")) {
            return;
        }

        this.setState({ isLoading: true });
        const isSuccess = await API.fileSystemDelete(fileSystemName);
        await this.adlsListFileSystems(); // Reload file systems
        this.setState({ isLoading: false });
    }

    async onClickSelectFileSystem(name) {
        this.setState({ isLoading: true });

        try {
            const fileSystemPaths = await API.getFileSystem(name);

            // fileSystemPaths: [{ etag, isDirectory, lastModified, name }]
            this.setState({ 
                selectedFileSystem: name, 
                paths: fileSystemPaths.sort((a, b) => 
                    ((b.isDirectory == 'true') || false) - ((a.isDirectory == 'true') || false) ||
                    a.name - b.name
                )
            });
        } catch (e) {
            console.log(JSON.parse(e.message));
            alert(e.message);
        }

        this.setState({ isLoading: false });
    }

    async loadPath(goToPath) {
        if (this.state.isLoading) {
            return;
        }
    
        this.setState({ isLoading: true });

        let newPath = goToPath;
        
        console.log(`Navigating from ${this.state.path} to ${newPath}`);

        const paths = await API.getFileSystemPath(this.state.selectedFileSystem, newPath);

        // fileSystemPaths: [{ etag, isDirectory, lastModified, name, contentLength }]
        this.setState({ 
            isLoading: false, 
            paths: paths.map((i) => ({ 
                name: i.name.replace(newPath + '/', ''),
                etag: i.etag,
                isDirectory: i.isDirectory || false,
                lastModified: i.lastModified,
                contentLength: i.contentLength || 0
            }))
            .sort((a, b) => 
                ((b.isDirectory == 'true') || false) - ((a.isDirectory == 'true') || false) ||
                a.name - b.name
            ), 
            path: newPath 
        })
    }

    async onClickNavigatePathUp() {
        const folders = this.state.path.split('/');
        const newPath = folders.slice(0, folders.length - 1).join('/');
        
        this.loadPath(newPath);
    }

    async onClickNavigatePath(path) {
        const newPath = `${this.state.path}/${path}`;
        this.loadPath(newPath)
    }

    async onClickFileDownload(name) {
        console.log(`Downloading ${this.state.path}/${name}`);
        await API.fileSystemFileDownload(this.state.selectedFileSystem, this.state.path, name);
    }

    async onClickFileDelete(fileName) {
        if (this.state.isLoading) {
            return;
        }

        if (!window.confirm("Are you sure you wish to delete this file?")) {
            return;
        }
    
        this.setState({ isLoading: true });
        await API.fileSystemFileDelete(this.state.selectedFileSystem, this.state.path, fileName);
        this.setState({ isLoading: false });
        this.loadPath(this.state.path);
    }

    async onClickFolderDelete(folderName) {
        if (this.state.isLoading) {
            return;
        }

        if (!window.confirm("Are you sure you wish to delete this folder?")) {
            return;
        }
    
        this.setState({ isLoading: true });
        await API.fileSystemFolderDelete(this.state.selectedFileSystem, this.state.path, folderName);
        this.setState({ isLoading: false });
        this.loadPath(this.state.path);
    }

    async onClickFolderCreate() {
        let folderName = prompt("Enter a Folder Name", "MyFolder");
        await API.fileSystemFolderCreate(this.state.selectedFileSystem, this.state.path, folderName);
        this.loadPath(this.state.path);
    }

    async onClickUploadContinue(e) {
        let input = document.querySelector('#adls-upload-file');

        if (!input || !input.files[0] || !input.files[0].name) {
            console.log('No file selected');
            return;
        }

        let inputBlob = input.files[0];
        let inputFileName = input.files[0].name;

        await API.fileSystemFileUpload(this.state.selectedFileSystem, this.state.path, inputFileName, inputBlob, this.cbOnUploadProgress.bind(this));
        this.loadPath(this.state.path);
    }

    async onClickUpload() {
        var input = document.querySelector('#adls-upload-file');
        input.click();
    }

    cbOnUploadProgress(total, current) {
        this.setState({ upload: { total, current} });

        if (total == current) {
            this.setState({ upload: undefined });
        }
    }

    render() {
        if (this.isLoading || !this.state.fileSystems) {
            return (<div>Loading...</div>)
        }

        if (!this.state.selectedFileSystem) {
            return this.renderListFileSystems();
        }

        return this.renderFileSystem();
    }

    renderListFileSystems() {
        return (
            <div className="ADLSGen2">
                {this.state.fileSystems.map((i) => <FileSystem 
                    name={i.name} 
                    onClick={(fileSystem) => this.onClickSelectFileSystem(fileSystem)}
                    onClickDelete={(fileSystem) => this.onClickFileSystemDelete(fileSystem)}
                    />)}
            </div>
        );
    }

    renderFileSystem() {
        return (
            <FileSystemPath>
                <input type="file" id="adls-upload-file" style={{ display: 'none' }} onChange={(e) => this.onClickUploadContinue(e)} />

                {/* Menu */}
                <Menu>
                    <MenuItem name="Create Folder" onClick={() => this.onClickFolderCreate()} />
                    {!this.state.upload && <MenuItem name="Upload" onClick={() => this.onClickUpload()} />}
                    {this.state.upload && <MenuItem name={<UploadProgress total={this.state.upload.total} current={this.state.upload.current} />} />}
                </Menu>

                {/* Folder up or Filesystem list */}
                {
                    this.state.path == "" ?
                        <FileSystemPathResourceFolder name="^ List Filesystems" onClick={() => this.adlsListFileSystems()} canDelete={false}/> :
                        <FileSystemPathResourceFolder name="..." onClick={() => this.onClickNavigatePathUp()} canDelete={false} />
                }

                {/* List files and folders */}
                {
                    this.state.paths.map((i) => 
                        (i.isDirectory) ?
                        <FileSystemPathResourceFolder 
                            name={i.name} 
                            onClick={(path) => this.onClickNavigatePath(path)} 
                            onClickDelete={(name) => this.onClickFolderDelete(name)} /> :
                        <FileSystemPathResourceFile 
                            name={i.name} 
                            onClick={() => console.log('is file')} 
                            onClickDownload={(name) => this.onClickFileDownload(name)} 
                            onClickDelete={(name) => this.onClickFileDelete(name)} />
                    )
                }
            </FileSystemPath>
        );
    }
}

export default ADLSGen2;
