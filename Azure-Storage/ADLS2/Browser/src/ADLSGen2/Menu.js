import React, { Component } from 'react';
import "./Menu.css";

class Menu extends Component {
    render() {
        return (
            <div className="ADLSGen2-Menu">
                {this.props.children}
            </div>
        );
    }
}

export default Menu;
