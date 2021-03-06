import React from 'react';
import PropTypes from 'prop-types';
import moment from 'moment-timezone';
import { get } from 'lodash';
import classNames from 'classnames';

import {SCHEDULE_TYPE} from '../utils';
import {bem} from 'ui/utils';
import {formatAgendaDate, formatDate, DATE_FORMAT, getScheduleType} from 'utils';

export default function AgendaTime({item, group, suppliedNodes, withGroupDate}) {
    const getClassNames = (modifier = 'event') => {
        return bem('wire-column__preview', 'date', modifier);
    };
    const startDateInRemoteTZ = moment.tz(moment(item.dates.start).utc(), item.dates.tz);
    const isRemoteTimezone = get(item, 'dates.tz') &&
        moment.tz(moment.tz.guess()).format('Z') !== startDateInRemoteTZ.format('Z');
    const getDates = (remoteTz = false) => {
        const isAllDay = getScheduleType(item) === SCHEDULE_TYPE.ALL_DAY;
        let dates;

        if (remoteTz) {
            if (!isRemoteTimezone) {
                return null;
            }

            const new_dates = {
                dates: {
                    start: startDateInRemoteTZ,
                    end: moment.tz(moment(item.dates.end).utc(), item.dates.tz),
                    tz: item.dates.tz,
                }
            };
            dates = formatAgendaDate(new_dates, group, false);
            return (<div key='remote-time' className={classNames(getClassNames(), getClassNames('remote'))}>
                {dates[0]} {dates[1]}
            </div>);
        } else {
            dates = formatAgendaDate(item, group);
        }

        if (suppliedNodes) {
            // Used in full-view mode where we supply a item label as suppliedNode
            return [(<div key='time' className={getClassNames(!isAllDay ? 'dashed-border' : 'event')}>
                {dates[1]} {dates[0]}</div>)];
        } else {
            const dateGroup = group && moment(group, DATE_FORMAT);
            let element = [<div key='time' className={getClassNames(!isAllDay ? 'dashed-border' : 'event')}>{dates[0]}</div>];
            if (dateGroup && withGroupDate && !isAllDay) {
                element.push((<div className= {classNames(getClassNames(), 'p-0')}>
                    {formatDate(dateGroup)}</div>));
            }

            return element;
        }
    };

    return [(<div key='local-time' className={classNames('wire-column__preview__content-header', {'mb-0': isRemoteTimezone}, {'mb-2': !isRemoteTimezone})}>
        <div className={classNames(getClassNames(),
            {'p-0': isRemoteTimezone})}>{getDates()}</div>
        {suppliedNodes}
    </div>),
    getDates(true)];
}

AgendaTime.propTypes = {
    item: PropTypes.object.isRequired,
    group: PropTypes.string,
    suppliedNodes: PropTypes.node,
    withGroupDate: PropTypes.bool,
};

AgendaTime.defaultProps = {
    withGroupDate: true
};
