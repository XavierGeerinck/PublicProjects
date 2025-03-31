import React, { Component } from 'react';
import PropTypes from 'prop-types';
import "./MenuItem.css";

class Menu extends Component {
    static propTypes = {
        name: PropTypes.string,
        onClick: PropTypes.func
    };

    static defaultProps = {
        onClick: () => {}
    };
    
    render() {
        return (
            <div className="ADLSGen2-MenuItem">
                <button onClick={(e) => this.props.onClick()}>{this.props.name}</button>
                {this.props.children}
            </div>
        );
    }
}

export default Menu;
