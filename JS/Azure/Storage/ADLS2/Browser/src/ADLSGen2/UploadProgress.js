import React, { Component } from 'react';
import PropTypes from "prop-types";
import "./FileSystemResources.css"

class FileSystemPath extends Component {
    static propTypes = {
    };


    render() {
        const { total, current } = this.props;

        if (total == current) {
            return null;
        }

        return (
            <div className="UploadProgress">
                <div>Progress: {Math.round(current / total * 100)}%</div>
            </div>
        );
    }
}

export default FileSystemPath;
